# Is that filtering and not slicing?

import torch
from models.olap_operations import OLAPOperation
from torch import nn

class SlicingModel(OLAPOperation):
    def __init__(self, slice_conditions):
        super(SlicingModel, self).__init__()
        self.slice_conditions = slice_conditions

    def forward(self, x):
        # create a mask of ones with the same size as the rows of x
        mask = torch.ones(x.size(0), dtype=torch.bool)
        for column, value in self.slice_conditions.items():
            # x[:, column] -> select all rows of the "column"
            mask = mask & (x[:, column] == value)
        return x * mask.unsqueeze(1) 
        # make zero the rows that do not match the conditions
        # Il modello lavora sempre su tensori di shape fissa, bisogna restituire un tensore con righe di 0
