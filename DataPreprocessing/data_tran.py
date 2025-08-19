import pandas as pd
import os
import json
import logging
from datetime import datetime

with open("config.json", "r") as file:
    config = json.load(file)

logging.basicConfig(
    filename=config["log_file"],
    level=logging.INFO,
    format="%(asctime)s - INFO - %(message)s",
)

def get_incremented_filename(filename):
    base, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename
    while os.path.exists(new_filename):
        new_filename = f"{base}_{counter}{ext}"
        counter += 1
    return new_filename

def data_transformation():
    input_csv = config["derived_data"]
    output_csv = config["transformed_data"]

    logging.info(f"Starting data transformation. Loading dataset from {input_csv}.")
    df = pd.read_csv(input_csv)

    if df.empty:
        logging.warning(f"{input_csv} is empty. Skipping data transformation.")
        return

    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    logging.info("Standardized column headers.")

    mappings = {
        "computer_user_role": {"Administrative Staff": 1, "Manager": 2, "Director": 3},
        "is_confidential": {"Confidential": 1, "Non-confidential": 0},
        "file_access_type": {
            "File Opening": 1,
            "File Modification": 2,
            "File Deletion": 3,
            "File Move": 4,
            "File Copy": 5
        },
        "computer_user_location": {"Room A": 1, "Room B": 2, "Room C": 3, "Room D": 4},
        "computer_room": {"Room A": 1, "Room C": 3, "Room D": 4}
    }

    for column, mapping in mappings.items():
        if column in df.columns:
            df[f"{column}_og"] = df[column]  # Save original
            df[column] = df[column].map(mapping).fillna(0).astype(int)
            logging.info(f"Encoded {column} using predefined mapping. Original preserved in {column}_og.")

    df["is_user_administrative_staff"] = (df["computer_user_role"] == 1).astype(int)
    df["is_user_manager"] = (df["computer_user_role"] == 2).astype(int)
    df["is_user_director"] = (df["computer_user_role"] == 3).astype(int)

    df["is_file_opening"] = (df["file_access_type"] == 1).astype(int)
    df["is_file_modification"] = (df["file_access_type"] == 2).astype(int)
    df["is_file_deletion"] = (df["file_access_type"] == 3).astype(int)
    df["is_file_move"] = (df["file_access_type"] == 4).astype(int)
    df["is_file_copy"] = (df["file_access_type"] == 5).astype(int)

    if "nearby_users" in df.columns:
        df["nearby_users"] = df["nearby_users"].fillna("")
        df["administrative_staff_presence"] = df["nearby_users"].apply(lambda x: 1 if "AS" in x else 0)
        df["manager_presence"] = df["nearby_users"].apply(lambda x: 1 if "Manager" in x else 0)
        df["director_presence"] = df["nearby_users"].apply(lambda x: 1 if "Director" in x else 0)

        logging.info("Processed nearby user role presence.")

    if {"timestamp", "shift_start", "shift_end"}.issubset(df.columns):
        def determine_shift_status(row):
            try:
                timestamp = datetime.fromisoformat(row["timestamp"]) if isinstance(row["timestamp"],
                                                                                   str) else datetime.fromtimestamp(
                    float(row["timestamp"]))
                shift_start = datetime.strptime(row["shift_start"], "%H:%M:%S").time()
                shift_end = datetime.strptime(row["shift_end"], "%H:%M:%S").time()
                return 1 if shift_start <= timestamp.time() <= shift_end else 0
            except Exception as e:
                logging.warning(f"Error processing shift status for row: {row} | Error: {e}")
                return 0

        df["shift_status"] = df.apply(determine_shift_status, axis=1)
        logging.info("Determined shift status for all records based on time only.")

    if {"computer_user_location", "computer_room"}.issubset(df.columns):
        df["room_mismatch"] = df.apply(
            lambda row: 0 if row["computer_user_location"] == row["computer_room"] else 1,
            axis=1
        )
        logging.info("Derived room_mismatch column based on computer_user_location and computer_room comparison.")

    if "break_status" in df.columns:
        df["is_on_break"] = df["break_status"].apply(lambda x: 1 if x == 1 else 0)
        logging.info("Derived is_on_break from break_status.")


    required_columns = [
        "shift_status", "computer_user_role",
        "is_user_administrative_staff", "is_user_manager", "is_user_director",
        "administrative_staff_presence", "manager_presence", "director_presence",
        "room_mismatch", "file_destination_type",
        "is_file_went_to_external_drive", "is_file_went_to_other_staff_drive",
        "is_file_went_to_internal_drive",
        "file_access_type",
        "is_file_opening", "is_file_modification", "is_file_deletion",
        "is_file_move", "is_file_copy",
        "is_confidential", "is_on_break"
    ]

    for col in required_columns:
        if col not in df.columns:
            df[col] = 0

    df = df[required_columns]
    logging.info("Rearranged dataset columns to match the required order.")

    output_csv = get_incremented_filename(output_csv)

    df.to_csv(output_csv, index=False)
    logging.info(f"Saved transformed data to {output_csv}.")
    logging.info(f"Data transformation completed. {df.shape[0]} rows processed.")

if __name__ == "__main__":
    data_transformation()
