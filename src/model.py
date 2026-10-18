import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models


class DocumentAngleModel(nn.Module):
    """
    Ultra-lightweight document orientation and tilt angle regressor.
    Uses MobileNetV3-Small backbone to output a unit vector [sin(theta), cos(theta)].
    Normalized to unit length to ensure stability and smooth gradient flow.
    """
    def __init__(self, backbone="large", pretrained=True):
        super().__init__()
        self.backbone_name = backbone.lower()
        if self.backbone_name == "small":
            weights = models.MobileNet_V3_Small_Weights.DEFAULT if pretrained else None
            self.backbone = models.mobilenet_v3_small(weights=weights)
        else:
            weights = models.MobileNet_V3_Large_Weights.DEFAULT if pretrained else None
            self.backbone = models.mobilenet_v3_large(weights=weights)
            
        in_features = self.backbone.classifier[0].in_features
        
        # Lightweight regression head for [sin(theta), cos(theta)]
        self.backbone.classifier = nn.Sequential(
            nn.Linear(in_features, 128),
            nn.Hardswish(),
            nn.Dropout(0.2),
            nn.Linear(128, 2)
        )

    def forward(self, x):
        out = self.backbone(x)
        # Normalize to unit circle: [sin(theta), cos(theta)]
        return F.normalize(out, p=2, dim=1)

    @staticmethod
    def sin_cos_to_angle(sin_val, cos_val):
        """
        Converts sin and cos tensors to angle in degrees [-180, 180].
        """
        angle_rad = torch.atan2(sin_val, cos_val)
        return torch.rad2deg(angle_rad)


def compute_angular_error_deg(pred_sin_cos, target_sin_cos):
    """
    Calculates the exact shortest angular error in degrees between pred and target unit vectors.
    Using cross product and dot product:
    sin(d_theta) = s1*c2 - c1*s2
    cos(d_theta) = c1*c2 + s1*s2
    d_theta = atan2(sin(d_theta), cos(d_theta))
    """
    s1, c1 = pred_sin_cos[:, 0], pred_sin_cos[:, 1]
    s2, c2 = target_sin_cos[:, 0], target_sin_cos[:, 1]
    
    sin_diff = s1 * c2 - c1 * s2
    cos_diff = c1 * c2 + s1 * s2
    
    angle_diff_rad = torch.atan2(sin_diff, cos_diff)
    angle_diff_deg = torch.abs(torch.rad2deg(angle_diff_rad))
    return angle_diff_deg
