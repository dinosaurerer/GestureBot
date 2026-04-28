# Ultralytics YOLO 🚀, AGPL-3.0 license
"""Efficient Local Attention (ELA) module.

Paper: ELA: Efficient Local Attention for Deep Convolutional Neural Networks (CVPR 2024)
       https://arxiv.org/abs/2403.01123
Code:  https://github.com/Xuwei86/ELA_Code
"""

import torch
import torch.nn as nn


class ELA(nn.Module):
    """Efficient Local Attention module.

    Uses 1D convolutions along spatial dimensions with Group Normalization to capture
    local spatial dependencies, generating attention weights without channel reduction.
    """

    def __init__(self, c1, kernel_size=7):
        """Initialize ELA module.

        Args:
            c1: Input channels.
            kernel_size: Kernel size for 1D convolutions (default 7).
        """
        super().__init__()
        # 1D convolution along X direction (width)
        self.conv_h = nn.Conv1d(c1, c1, kernel_size, padding=kernel_size // 2, groups=1)
        # 1D convolution along Y direction (height)
        self.conv_w = nn.Conv1d(c1, c1, kernel_size, padding=kernel_size // 2, groups=1)
        # Group Normalization
        self.gn = nn.GroupNorm(num_groups=min(16, c1), num_channels=c1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        """Apply efficient local attention.

        Args:
            x: Input tensor of shape (B, C, H, W).

        Returns:
            Attention-weighted tensor of same shape.
        """
        # X-direction attention: average pool along H → 1D conv along W
        x_h = self.conv_h(x.mean(dim=2))  # (B, C, W)
        x_h = self.sigmoid(self.gn(x_h.unsqueeze(2))).squeeze(2)  # (B, C, W)
        # Y-direction attention: average pool along W → 1D conv along H
        x_w = self.conv_w(x.mean(dim=3))  # (B, C, H)
        x_w = self.sigmoid(self.gn(x_w.unsqueeze(3))).squeeze(3)  # (B, C, H)
        # Element-wise multiply
        return x * x_h.unsqueeze(2) * x_w.unsqueeze(3)
