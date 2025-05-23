# Is that filtering and not slicing?

# Example: SlicingModel({14: 1, 21: 12, 27: 0})
# -> filter to have only the rows where column 14 is ==1, column 21 is ==12 and column 27 is ==0

import torch
from models.olap_operations import OLAPOperation
from torch import nn

class FilteringModel(OLAPOperation):
    def __init__(self, filter_conditions):
        super(FilteringModel, self).__init__()
        self.filter_conditions = filter_conditions

    def forward(self, x):
        # create a mask of ones with the same size as the rows of x
        mask = torch.ones(x.size(0), dtype=torch.bool)
        for column, value in self.filter_conditions.items():
            # x[:, column] -> select all rows of the "column"
            mask = mask & (x[:, column] == value)
        return x * mask.unsqueeze(1) 
        # make zero the rows that do not match the conditions
        # Il modello lavora sempre su tensori di shape fissa, bisogna restituire un tensore con righe di 0
