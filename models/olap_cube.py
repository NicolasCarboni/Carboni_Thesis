import torch
from torch import nn
from sklearn.preprocessing import LabelEncoder

class OLAPCube:
    def __init__(self, df):
        self.df = df
        self.label_encoder = LabelEncoder()
        self.category_mappings = self.encode_categorical_columns()

    def encode_categorical_columns(self):
        categorical_columns = self.df.select_dtypes(include=['object']).columns
        category_mappings = {}
        for col in categorical_columns:
            self.df[col] = self.label_encoder.fit_transform(self.df[col].astype(str))
            category_mappings[col] = dict(zip(self.label_encoder.classes_, self.label_encoder.transform(self.label_encoder.classes_)))
        return category_mappings

    def to_tensor(self):
        return torch.tensor(self.df.values, dtype=torch.float32)

    def execute_model(self, model, tensor_data):
        return model(tensor_data)
