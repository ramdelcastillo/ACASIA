import pandas as pd
import os
import json
import logging

with open("config.json", "r") as file:
    config = json.load(file)

logging.basicConfig(
    filename=config["log_file"],
    level=logging.INFO,
    format="%(asctime)s - INFO - %(message)s",
)

def data_derivation():
    input_csv = config["imputed_data"]
    config_db = config["config_db"]
    output_csv = config["derived_data"]

    logging.info(f"Loading dataset from {input_csv} and configuration from {config_db}.")

    df = pd.read_csv(input_csv)
    config_data = pd.read_csv(config_db)

    if df.empty:
        logging.warning(f"{input_csv} is empty. Skipping data derivation.")
        return

    config_data.columns = config_data.columns.str.strip().str.lower().str.replace(" ", "_")
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    df["username"] = df["username"].str.strip().str.lower()
    config_data["user_name"] = config_data["user_name"].str.strip().str.lower()

    logging.info("Standardized column headers and usernames.")

    column_mappings = {
        "user_name": "username",
        "user_role": "computer_user_role",
        "shift_start": "shift_start",
        "shift_end": "shift_end",
    }
    config_data.rename(columns=column_mappings, inplace=True)

    if "computer_user_role" not in config_data.columns or "username" not in df.columns:
        logging.error("Missing required columns in configuration or dataset.")
        raise KeyError("Missing 'computer_user_role' in config_db or 'username' in input_csv")

    user_role_mapping = config_data.set_index("username")["computer_user_role"].to_dict()
    df["computer_user_role"] = df["username"].map(user_role_mapping).fillna("Unknown")
    logging.info("Mapped usernames to computer user roles.")

    role_mapping = config_data.set_index("username")[["shift_start", "shift_end"]].to_dict()
    df["shift_start"] = df["username"].map(role_mapping["shift_start"]).fillna("unknown")
    df["shift_end"] = df["username"].map(role_mapping["shift_end"]).fillna("unknown")
    logging.info("Mapped computer users to shift.")

    def convert_quotes(nearby_users):
        if pd.isnull(nearby_users) or nearby_users.strip() == "":
            return "Unknown"
        try:
            return nearby_users.replace('"', "'")
        except Exception as e:
            logging.warning(f"Error converting nearby_users quotes: {nearby_users} | Error: {e}")
            return "Unknown"

    df["nearby_users"] = df["nearby_users"].apply(convert_quotes)
    logging.info("Standardized quotes in nearby_users.")

    def get_confidentiality(file_name):
        if pd.isnull(file_name) or not isinstance(file_name, str):
            return "Unknown"
        file_name = file_name.strip()
        base_name, ext = os.path.splitext(file_name)
        return "Non-confidential" if "NON" in base_name else "Confidential"

    df["is_confidential"] = df["file_destination_directory"].apply(get_confidentiality)
    logging.info("Classified files as Confidential or Non-confidential.")

    def classify_file_destination_type(directory):
        if isinstance(directory, str):
            dir_lower = directory.lower()
            if "external" in dir_lower:
                return 2
            elif "others" in dir_lower:
                return 3
        return 1

    df["file_destination_type"] = (
        df["file_destination_directory"].apply(classify_file_destination_type))

    def set_file_destination_flags(directory):
        dir_lower = directory.lower()
        is_external = int("external" in dir_lower)
        is_other = int("others" in dir_lower)
        is_internal = int(not is_external and not is_other)
        return pd.Series({
            "is_file_went_to_external_drive": is_external,
            "is_file_went_to_other_staff_drive": is_other,
            "is_file_went_to_internal_drive": is_internal
        })

    df[["is_file_went_to_external_drive", "is_file_went_to_other_staff_drive",
        "is_file_went_to_internal_drive"]] = df[
        "file_destination_directory"].apply(set_file_destination_flags)

    logging.info("Classified file destination type (external/others/internal).")

    df.to_csv(output_csv, index=False)
    logging.info(f"Data derivation completed. Saved to {output_csv}. {df.shape[0]} rows processed.")

if __name__ == "__main__":
    data_derivation()
