import torch
from torch import nn
from sklearn.preprocessing import LabelEncoder # to convert categorical string data into numeric labels
import json

class OLAPCube:
    def __init__(self, df, category_mappings=None): # The constructor receives as input a >..
        self.df = df                                #  ..< pandas DataFrame (df) 
        self.label_encoder = LabelEncoder() # Initialize an instance of LabelEncoder, which is then assigned to the attribute label_encoder
        if category_mappings is not None:
            self.category_mappings = category_mappings
            # Encode columns using the provided mapping
            for col, mapping in self.category_mappings.items():
                #? inv_mapping = {v: k for k, v in mapping.items()}
                self.df[col] = self.df[col].map(lambda x: mapping.get(str(x), x))
        else:
            self.category_mappings = self.encode_categorical_columns()

    def encode_categorical_columns(self):
        categorical_columns = self.df.select_dtypes(include=['object']).columns
        category_mappings = {}
        for col in categorical_columns:
            self.df[col] = self.label_encoder.fit_transform(self.df[col].astype(str))
            # Convert mapping values to native int
            mapping = dict(zip(
                self.label_encoder.classes_,
                [int(x) for x in self.label_encoder.transform(self.label_encoder.classes_)]
            ))
            category_mappings[col] = mapping
        return category_mappings
    
    def save_category_mappings(self, path):
        with open(path, "w") as f:
            json.dump(self.category_mappings, f) 
    
    """
    def encode_categorical_columns(self): # called in the construction
        # Select all columns with object data type (typically strings), categorical_columns is the list of column names that are categorical
        categorical_columns = self.df.select_dtypes(include=['object']).columns
        category_mappings = {} # Initialize an empty dictionary to store the mappings
        for col in categorical_columns:
            # Transform the categorical column into numeric labels using LabelEncoder
            self.df[col] = self.label_encoder.fit_transform(self.df[col].astype(str))
            category_mappings[col] = dict(zip(self.label_encoder.classes_, self.label_encoder.transform(self.label_encoder.classes_)))
        return category_mappings
    
    def save_category_mappings(self, path):
        def convert(obj): # This function is used to convert the values of the DataFrame to a format that can be serialized to JSON
            if isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert(v) for v in obj]
            elif hasattr(obj, "item"):
                return int(obj)
            else:
                return int(obj) if isinstance(obj, float) and obj.is_integer() else obj
        
        with open(path, "w") as f:
            json.dump(convert(self.category_mappings), f)    
    """

    def load_category_mappings(path):
        with open(path, "r") as f:
            return json.load(f)
    
    def decode_categorical_columns(self):
        decoded_df = self.df.copy()
        for col, mapping in self.category_mappings.items():
            inv_mapping = {v: k for k, v in mapping.items()}
            decoded_df[col] = decoded_df[col].map(inv_mapping)
        return decoded_df

    # This method is used to convert the values of the DataFrame to a torch tensor of type float32
    def to_tensor(self):    
        return torch.tensor(self.df.values, dtype=torch.float32)

    # This method applies a specified operation (model) to the tensor data
    def execute_model(self, model, tensor_data):
        return model(tensor_data) # slicing/ roll_op/ dicing_model
    # In PyTorch, any class that inherits from nn.Module can be called like a function (i.e., model(tensor_data)), which internally calls its forward() method.
    # So, model(tensor_data) is equivalent to model.forward(tensor_data)