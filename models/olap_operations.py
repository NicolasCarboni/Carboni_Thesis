from torch import nn


class OLAPOperation(nn.Module):
    def __init__(self):
        super(OLAPOperation, self).__init__()

    def forward(self, x):
        raise NotImplementedError("Subclasses should implement this method")
