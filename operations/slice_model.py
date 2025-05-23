from models.olap_operations import OLAPOperation
from torch import nn
import torch

class SliceModel(OLAPOperation):
    def __init__(self, remove_columns=None):
        super(SliceModel, self).__init__()
        self.remove_columns = sorted(remove_columns) if remove_columns is not None else []

    def forward(self, x):
        if not self.remove_columns:
            return x  # Nessuna colonna da rimuovere, ritorna x inalterato
        
        # Crea una lista di intervalli per mantenere le colonne
        ranges_to_keep = []
        start = 0
        for col in self.remove_columns:
            if col > start:
                ranges_to_keep.append((start, col))
            start = col + 1
        
        # Aggiungi l'ultimo intervallo se c'è ancora qualcosa dopo l'ultima colonna rimossa
        if start < x.size(1):
            ranges_to_keep.append((start, x.size(1)))
        
        # Concatena le parti da mantenere
        x_kept_parts = [x[:, s:e] for s, e in ranges_to_keep]
        print(f"Kept parts: {x_kept_parts}")
        return torch.cat(x_kept_parts, dim=1)