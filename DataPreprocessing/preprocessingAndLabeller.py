import os, re
import logging
import json
from data_imp import create_or_append_csv, data_imputation
from data_der import data_derivation
from data_tran import data_transformation
import time
import subprocess

with open("config.json", "r") as file:
    config = json.load(file)

logging.basicConfig(
    filename=config["log_file"],
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

dataPreprocessingDirectory = os.path.dirname(os.path.abspath(__file__))
baseProjectFolderDirectory = base_dir = (
    os.path.abspath(os.path.join(dataPreprocessingDirectory, "..")))
directoriesAccess = os.path.join(baseProjectFolderDirectory, "directories.json")

with open(directoriesAccess, "r") as f:
    directoryAccess = json.load(f)

labeller = directoryAccess["labeller"]
dataset_for_labelling = directoryAccess["data_sets_for_labelling"]
labelled_directory = directoryAccess["data_sets_labelled"]

def get_latest_transformed_file(input_folder):
    pattern = re.compile(r"^transformed(?:_(\d+))?\.csv$")
    candidates = []

    for filename in os.listdir(input_folder):
        match = pattern.match(filename)
        if match:
            number = int(match.group(1)) if match.group(1) else 0
            candidates.append((number, filename))

    if not candidates:
        raise FileNotFoundError("No transformed CSV files found in the folder.")

    candidates.sort(key=lambda x: x[0], reverse=True)
    latest_file = candidates[0][1]

    return os.path.join(input_folder, latest_file)

def run_pipeline():
    try:
        logging.info("=== Step 1: Running Data Imputation ===")
        create_or_append_csv()
        logging.info("Raw data loaded into CSV.")

        data_imputation()
        logging.info("Data Imputation Completed Successfully.")

        logging.info("=== Step 2: Running Data Derivation ===")
        data_derivation()
        logging.info("Data Derivation Completed Successfully.")

        logging.info("=== Step 3: Running Data Transformation ===")
        data_transformation()
        logging.info("Data Transformation Completed Successfully.")

        logging.info("=== Pipeline Execution Completed ===")

        time.sleep(5)
        logging.info("=== Step 4: Labelling Dataset ===")

        transformed_dataset = get_latest_transformed_file(dataset_for_labelling)
        subprocess.run(["python", labeller, transformed_dataset])

        print("Data preprocessing and labelling completed.")

    except Exception as e:
        logging.error(f"Pipeline execution failed: {e}")
        print("Error encountered! Check preprocessing.log for details.")

if __name__ == "__main__":
    json_file = config["json_file"]

    if os.path.exists(json_file):
        print(f"Running preprocessing pipeline on '{json_file}'...\n")
        run_pipeline()
    else:
        print(f"File '{json_file}' not found. Exiting.")
