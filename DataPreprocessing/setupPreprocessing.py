import os

dataPreprocessingDirectory = os.path.dirname(os.path.abspath(__file__))

files_to_delete = [
    "derived_data.csv",
    "imputed_data.csv",
    "raw_data_unprocessed.csv",
    "raw_data.csv",
    "preprocessing.log",
    "last_processed_log.txt"
]

for file in files_to_delete:
    file_path = os.path.join(dataPreprocessingDirectory, file)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"Deleted: {file_path}")
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")
    else:
        print(f"File not found: {file_path}")
