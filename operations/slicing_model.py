import torch
from models.olap_operations import OLAPOperation
from torch import nn

class SlicingModel(OLAPOperation):
    def __init__(self, slice_conditions):
        super(SlicingModel, self).__init__()
        self.slice_conditions = slice_conditions

    def forward(self, x):
        mask = torch.ones(x.size(0), dtype=torch.bool)
        for column, value in self.slice_conditions.items():
            mask = mask & (x[:, column] == value)
        return x * mask.unsqueeze(1)
