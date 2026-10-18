# Contributing

Thank you for looking at docangle. The project's rule is that **nothing changes the default behaviour without a paired measurement**, and this file says how to produce one.

## Set up

```bash
pip install -e ".[dev,pdf]"
pytest -q                          # unit tests; tests that need benchmark images skip themselves when data/ is absent
ruff check .                       # syntax errors and pyflakes (unused or undefined names); no style rules
python -m tools.gen_config_doc --check
python -m tools.check_links        # relative links, #anchors and repository paths named in the Markdown files
```

## Changing the algorithm

1. Read [`docs/02-design.md`](docs/02-design.md) and [`docs/11-decisions.md`](docs/11-decisions.md): the idea may have been tried.
2. Put your change behind a `PipelineConfig` field (default = old behaviour) and add a candidate to `bench/candidates.py`.
3. Compare it with the default on the same cases: `python -m bench.guard --base docangle --variants yourcandidate --datasets tobacco_cert rvl_heldout ext_funsd --levels scan photo_hard --n 100` (the pools are recreated as described in `docs/12-reproduce.md` 12.2; `az` and `invoices` are private, use your own pages instead). A speed change is accepted only if at least 99 % of angles move by 0.05° or less and no accuracy metric drops; an accuracy change must improve the paired page-cluster interval, not just the mean (see `docs/04-evaluation-protocol.md`).
4. For a change that must not alter results (speed, refactoring) prove it per case with `bench.equiv dump` / `bench.equiv compare`.
5. Add a row to `docs/11-decisions.md` whatever the outcome; rejected experiments are as valuable as accepted ones.
6. If the change touches a documented default, update the chapter and run `python -m tools.gen_config_doc`.

## Data

Do not add images of documents you do not own or may not redistribute, and no pages from the research-only data sets (RVL-CDIP, Tobacco, FUNSD). Benchmark inputs are rebuilt by script from their public sources (`docs/12-reproduce.md`). Test fixtures must be synthetic.

## Reporting a problem

Open an issue with the command, the version (`python -c "import docangle; print(docangle.__version__)"`), the library versions and, if you can share it, the page. A wrong quadrant that was *not* sent to review is the most valuable report: say what the page is (script, layout, photo or scan).

## Style

Match the surrounding code: short comments that say why, no dead code, tests next to the behaviour they pin. Results go into `reports/` with the commit, configuration and library versions stored in the file (the harnesses do this).
