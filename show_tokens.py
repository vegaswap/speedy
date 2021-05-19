import importlib

module = importlib.import_module('token_addresses')
all_imported_data = {}
all_imported_data.update({k: v for k, v in module.__dict__.items() if not k.startswith('_')})
print(all_imported_data)
#print (module.__dict__.items())
