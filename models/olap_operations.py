# This class is an abstract template for OLAP operations
from torch import nn


class OLAPOperation(nn.Module): # inherits from nn.Module, making it compatible with PyTorch's neural network framework
    def __init__(self):
        super(OLAPOperation, self).__init__() # calls the parent constructor to properly initialize the PyTorch module

    def forward(self, x): # This method is meant to be overridden by subclasses
        raise NotImplementedError("Subclasses should implement this method")
