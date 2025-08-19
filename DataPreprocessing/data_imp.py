import json
import pandas as pd
import os
import logging

with open("config.json", "r") as file:
    config = json.load(file)

logging.basicConfig(
    filename=config["log_file"],
    level=logging.INFO,
    format="%(asctime)s - INFO - %(message)s",
)

def create_or_append_csv():
    json_file = config["json_file"]
    raw_csv = config["raw_data"]
    tracker_file = config["tracker_file"]

    try:
        with open(json_file, 'r') as file:
            data = json.load(file)
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON file: {e}")
        raise ValueError("Invalid JSON format")

    if not isinstance(data, list):
        logging.warning(f"Unexpected format in {json_file}. Expected a list of logs.")
        return False

    df = pd.DataFrame(data)

    df.to_csv(raw_csv, index=False)
    logging.info(f"Wrote all {df.shape[0]} logs to {raw_csv}.")

    with open(tracker_file, "w") as f:
        f.write(str(len(data)))
    logging.info(f"Updated tracker file with {len(data)} logs.")

    return True


def data_imputation():
    raw_csv = config["raw_data"]
    imputed_csv = config["imputed_data"]
    backup_csv = config["backup_data"]

    if not os.path.exists(raw_csv) or os.stat(raw_csv).st_size == 0:
        logging.warning(f"No data in {raw_csv}. Skipping imputation.")
        return

    df = pd.read_csv(raw_csv)
    logging.info(f"Loaded raw data from {raw_csv}. {df.shape[0]} rows, {df.shape[1]} columns.")

    if os.path.exists(backup_csv):
        df.to_csv(backup_csv, mode="a", header=False, index=False)
        logging.info(f"Appended raw data to backup: {backup_csv}. {df.shape[0]} rows added.")
    else:
        df.to_csv(backup_csv, index=False)
        logging.info(f"Created backup file: {backup_csv}. {df.shape[0]} rows saved.")

    column_renames = {
        "logID": "log_id",
        "Timestamp": "timestamp",
        "Username": "username",
        "ComputerID": "computer_id",
        "fileAccessType": "file_access_type",
        "fileDestinationDirectory": "file_destination_directory",
        "breakStatus": "break_status",
        "NearbyUsers": "nearby_users",
        "ActualLocationOfUsername": "computer_user_location",
        "ComputerRoom": "computer_room",
    }

    df.rename(columns={col: new_col for col, new_col in column_renames.items() if col in df.columns}, inplace=True)

    for old_col, new_col in column_renames.items():
        if old_col in df.columns:
            logging.info(f"Renamed '{old_col}' to '{new_col}'.")

    for column in df.columns:
        if df[column].isnull().any():
            before_missing = df[column].isnull().sum()

            if column == "timestamp":
                df[column] = df[column].fillna(method="ffill").fillna(method="bfill")
            elif column == "computer_id":
                df[column].fillna(df[column].median(), inplace=True)
            elif column == "username":
                df[column].fillna(df[column].mode()[0]
                                  if not df[column].mode().empty else "Unknown", inplace=True)
            elif column == "computer_user_location":
                df[column].fillna(df[column].mode()[0]
                                  if not df[column].mode().empty else "Unknown", inplace=True)
            elif column == "computer_room":
                df[column].fillna(df[column].mode()[0]
                                  if not df[column].mode().empty else "Unknown", inplace=True)
            elif column == "file_access_type":
                df[column].fillna(df[column].mode()[0]
                                  if not df[column].mode().empty else "Unknown", inplace=True)
            elif column == "file_destination_directory":
                df[column].fillna("Unknown Directory", inplace=True)
            elif column == "break_status":
                df[column].fillna(df[column].mode()[0]
                                  if not df[column].mode().empty else "Unknown", inplace=True)
            elif column == "nearby_users":
                df[column] = df[column].apply(lambda x: x if isinstance(x, list) else [])

            after_missing = df[column].isnull().sum()
            logging.info(f"Filled {before_missing - after_missing} missing values in '{column}'.")

    df["nearby_users"] = df["nearby_users"].apply(lambda x: [] if x == "[]" else x)
    before_rows = df.shape[0]
    df = df[df["nearby_users"].apply(lambda x: len(x) > 0)]
    dropped_rows = before_rows - df.shape[0]
    logging.info(f"Dropped {dropped_rows} rows where nearby_users was an empty list.")

    df.to_csv(imputed_csv, index=False)
    logging.info(f"Saved imputed data to {imputed_csv}. {df.shape[0]} rows processed.")

if __name__ == "__main__":
    create_or_append_csv()
    data_imputation()
