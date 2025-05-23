from models.olap_operations import OLAPOperation
import torch
from torch import nn

class DicingModel(OLAPOperation):
    def __init__(self, conditions):
        super(DicingModel, self).__init__()
        self.conditions = conditions

    def forward(self, x):
        mask = torch.ones(x.size(0), dtype=torch.bool)
        for column, value in self.conditions.items():
            if isinstance(value, list):
                temp_mask = torch.zeros(x.size(0), dtype=torch.bool)
                for val in value:
                    temp_mask = temp_mask | (x[:, column] == val)
                mask = mask & temp_mask
            else:
                mask = mask & (x[:, column] == value)
        return x * mask.unsqueeze(1)
    