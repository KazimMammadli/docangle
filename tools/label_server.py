#!/usr/bin/env python3
"""Local labeling tool for real photos (stdlib only).

    python tools/label_server.py PHOTO_DIR [--out labels.jsonl] [--port 8765]

Open http://127.0.0.1:8765 . For each image drag a line ALONG ONE LINE OF TEXT IN READING DIRECTION
(first letter -> last letter, as a person would read it). That single drag defines the ground truth:
    angle = -atan2(dy, dx)   (image y points down; CCW-positive, same convention as docangle)
so 0 deg = upright, 180 = upside down, +90 = text runs bottom-to-top, etc.
Longer drags are more accurate; use a line of at least ~1/3 of the page width.
Buttons: Skip (not a document / unreadable), No text (blank/photo page), Undo, arrow keys to navigate.
Labels are appended to a JSONL file; the last label for a file wins. Images are never modified.
"""
import argparse
import json
import math
import os
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

EXT = (".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff")

PAGE = r"""<!doctype html><meta charset=utf-8><title>Angle labeling</title>
<style>
body{font:14px system-ui;margin:0;background:#1d1d1f;color:#eee}
#bar{display:flex;gap:8px;align-items:center;padding:8px 12px;background:#2b2b2e;position:sticky;top:0}
button{padding:6px 12px;border:0;border-radius:6px;background:#4a4a50;color:#fff;cursor:pointer}
button:hover{background:#5d5d66} #info{margin-left:auto;opacity:.8}
canvas{display:block;margin:8px auto;background:#000;cursor:crosshair;max-width:100%}
</style>
<div id=bar><button id=prev>&larr; Prev</button><button id=next>Next &rarr;</button>
<button id=undo>Undo</button><button id=notext>No text</button><button id=skip>Skip</button>
<span id=msg></span><span id=info></span></div><canvas id=c></canvas>
<script>
let files=[],labels={},i=0,img=new Image(),p0=null,p1=null,scale=1,drag=false;
const c=document.getElementById('c'),x=c.getContext('2d');
const $=id=>document.getElementById(id);
async function init(){files=await (await fetch('/api/files')).json();labels=await (await fetch('/api/labels')).json();
 i=Math.max(0,files.findIndex(f=>!(f in labels)));load();}
function load(){p0=p1=null;img=new Image();img.onload=draw;img.src='/img/'+encodeURIComponent(files[i]);info();}
function info(){const l=labels[files[i]];const n=Object.keys(labels).length;
 $('info').textContent=`${i+1}/${files.length}  labeled ${n}  `+files[i]+(l?`  -> ${l.status==='ok'?l.angle.toFixed(2)+'°':l.status}`:'');}
function draw(){const maxW=Math.min(innerWidth-20,1400),maxH=innerHeight-70;scale=Math.min(maxW/img.width,maxH/img.height,2.5);
 c.width=img.width*scale;c.height=img.height*scale;x.drawImage(img,0,0,c.width,c.height);
 const l=labels[files[i]];if(!p0&&l&&l.status==='ok'&&l.line){p0=l.line.slice(0,2).map(v=>v*scale);p1=l.line.slice(2).map(v=>v*scale);}
 if(p0&&p1){x.strokeStyle='#ff3b30';x.lineWidth=2;x.beginPath();x.moveTo(...p0);x.lineTo(...p1);x.stroke();
  const a=Math.atan2(p1[1]-p0[1],p1[0]-p0[0]);x.fillStyle='#ff3b30';x.beginPath();x.moveTo(...p1);
  x.lineTo(p1[0]-12*Math.cos(a-.4),p1[1]-12*Math.sin(a-.4));x.lineTo(p1[0]-12*Math.cos(a+.4),p1[1]-12*Math.sin(a+.4));x.fill();}}
function pos(e){const r=c.getBoundingClientRect();return [(e.clientX-r.left)*c.width/r.width,(e.clientY-r.top)*c.height/r.height];}
c.onmousedown=e=>{p0=pos(e);p1=null;drag=true;};
c.onmousemove=e=>{if(drag){p1=pos(e);x.drawImage(img,0,0,c.width,c.height);draw();}};
c.onmouseup=async e=>{drag=false;p1=pos(e);const dx=(p1[0]-p0[0])/scale,dy=(p1[1]-p0[1])/scale,len=Math.hypot(dx,dy);
 if(len<img.width*0.12){$('msg').textContent='line too short - drag along a whole text line';p0=p1=null;draw();return;}
 const angle=-Math.atan2(dy,dx)*180/Math.PI;
 await save({status:'ok',angle:angle,line:[p0[0]/scale,p0[1]/scale,p1[0]/scale,p1[1]/scale],len_frac:len/img.width});};
async function save(l){l.file=files[i];await fetch('/api/label',{method:'POST',body:JSON.stringify(l)});labels[files[i]]=l;$('msg').textContent='saved';
 if(i<files.length-1){i++;load();}else{info();draw();}}
$('next').onclick=()=>{if(i<files.length-1){i++;load();}};$('prev').onclick=()=>{if(i>0){i--;load();}};
$('skip').onclick=()=>save({status:'skip'});$('notext').onclick=()=>save({status:'no_text'});
$('undo').onclick=async()=>{await fetch('/api/label',{method:'DELETE',body:JSON.stringify({file:files[i]})});delete labels[files[i]];p0=p1=null;draw();info();};
onkeydown=e=>{if(e.key==='ArrowRight')$('next').click();if(e.key==='ArrowLeft')$('prev').click();};
init();
</script>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("photo_dir")
    ap.add_argument("--out", default="labels.jsonl")
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()
    root = os.path.abspath(args.photo_dir)
    files = sorted(f for f in os.listdir(root) if f.lower().endswith(EXT))
    if not files:
        sys.exit("no images in " + root)

    def load_labels():
        d = {}
        if os.path.exists(args.out):
            for line in open(args.out, encoding="utf-8"):
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if r.get("deleted"):
                    d.pop(r["file"], None)
                else:
                    d[r["file"]] = r
        return d

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, code, body, ctype="application/json"):
            b = body if isinstance(body, bytes) else body.encode()
            self.send_response(code); self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

        def do_GET(self):
            u = urllib.parse.urlparse(self.path).path
            if u == "/":
                return self._send(200, PAGE, "text/html; charset=utf-8")
            if u == "/api/files":
                return self._send(200, json.dumps(files))
            if u == "/api/labels":
                return self._send(200, json.dumps(load_labels()))
            if u.startswith("/img/"):
                name = os.path.basename(urllib.parse.unquote(u[5:]))
                p = os.path.join(root, name)
                if name in files and os.path.isfile(p):
                    ct = "image/png" if name.lower().endswith(".png") else "image/jpeg"
                    return self._send(200, open(p, "rb").read(), ct)
            self._send(404, "{}")

        def _body(self):
            return json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")

        def do_POST(self):
            r = self._body()
            if r.get("file") not in files:
                return self._send(400, "{}")
            if r.get("status") == "ok" and not math.isfinite(r.get("angle", float("nan"))):
                return self._send(400, "{}")
            with open(args.out, "a", encoding="utf-8") as f:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
            self._send(200, "{}")

        def do_DELETE(self):
            r = self._body()
            with open(args.out, "a", encoding="utf-8") as f:
                f.write(json.dumps({"file": r.get("file"), "deleted": True}) + "\n")
            self._send(200, "{}")

    srv = ThreadingHTTPServer(("127.0.0.1", args.port), H)
    print(f"{len(files)} images. Open http://127.0.0.1:{args.port}  (labels -> {args.out})")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
