import torch
from torch import nn
from sklearn.preprocessing import LabelEncoder # to convert categorical string data into numeric labels

class OLAPCube:
    def __init__(self, df): # The constructor receives a >
        self.df = df        #  < pandas DataFrame (df) as input
        self.label_encoder = LabelEncoder() # Initialize an instance of LabelEncoder, which is then assigned to the attribute label_encoder
        self.category_mappings = self.encode_categorical_columns() # Call the encode_categorical_columns method defined in the class

    def encode_categorical_columns(self): # called in the construction
        # Select all columns with object data type (typically strings), categorical_columns is the list of column names that are categorical
        categorical_columns = self.df.select_dtypes(include=['object']).columns
        category_mappings = {} # Initialize an empty dictionary to store the mappings
        for col in categorical_columns:
            # Transform the categorical column into numeric labels using LabelEncoder
            self.df[col] = self.label_encoder.fit_transform(self.df[col].astype(str))
            category_mappings[col] = dict(zip(self.label_encoder.classes_, self.label_encoder.transform(self.label_encoder.classes_)))
        return category_mappings
    
    """"
    def decode_categorical_columns(self):
        decoded_df = self.df.copy()
        for col, mapping in self.category_mappings.items():
            inv_mapping = {v: k for k, v in mapping.items()}
            decoded_df[col] = decoded_df[col].map(inv_mapping)
        return decoded_df
    """

    # This method is used to convert the values of the DataFrame to a torch tensor of type float32
    def to_tensor(self):    
        return torch.tensor(self.df.values, dtype=torch.float32)

    # This method applies a specified operation (model) to the tensor data
    def execute_model(self, model, tensor_data):
        return model(tensor_data) # slicing/ roll_op/ dicing_model
    # In PyTorch, any class that inherits from nn.Module can be called like a function (i.e., model(tensor_data)), which internally calls its forward() method.
    # So, model(tensor_data) is equivalent to model.forward(tensor_data)