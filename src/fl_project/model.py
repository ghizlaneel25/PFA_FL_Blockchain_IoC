import torch
import torch.nn as nn
from opacus.layers import DPLSTM

class CNN_LSTM(nn.Module):
    def __init__(self, input_size, num_classes):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv1d(1, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool1d(2)
        )
        self.lstm = DPLSTM(64, 128, batch_first=True, bidirectional=True)
        self.fc = nn.Sequential(
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, num_classes)
        )

    def forward(self, x):
        x = x.unsqueeze(1)
        x = self.conv(x)
        x = x.transpose(1, 2)
        x, _ = self.lstm(x)
        return self.fc(x[:, -1, :])
