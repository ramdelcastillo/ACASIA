import json
import os
import sys
import logging
import pandas as pd

logging.basicConfig(
    filename="labelling.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

datasetLabellingDirectory = os.path.dirname(os.path.abspath(__file__))
baseProjectFolderDirectory = base_dir = os.path.abspath(os.path.join(datasetLabellingDirectory, ".."))
directoriesAccess = os.path.join(baseProjectFolderDirectory, "directories.json")

with open(directoriesAccess, "r") as f:
    directoryAccess = json.load(f)

labelled_directory = directoryAccess["data_sets_labelled"]

def set_authorized(df):
    df['authorized'] = df.apply(handle_authorized, axis=1)
    return df

def handle_authorized(row):
    # SCENARIO 1: SHIFT TIME; SCENARIO 2: ROOM MISMATCH
    if row['shift_status'] == 0 or row['room_mismatch'] == 1:
        return 0

    # SCENARIO 3: Moving/copying files to external storages
    # AUTHORIZED
    # Directors move and copy confidential or non-confidential files to external storages
    if row['computer_user_role'] == 3 and row['file_access_type'] in [4, 5] and row['file_destination_type'] == 2:
        return 1

    # Managers copy non-confidential or confidential files to external storages without permission from the Director
    if row['computer_user_role'] == 2 and row['file_access_type'] == 5 and row['file_destination_type'] == 2:
        return 1

    # Managers move non-confidential or confidential files to external storages with permission from the Director
    if row['computer_user_role'] == 2 and row['file_access_type'] == 4 and row['file_destination_type'] == 2:
        if row['director_presence'] == 1:
            return 1

    # Administrative Staff copy non-confidential and confidential files to external storages with permission from Manager or Director.
    if row['computer_user_role'] == 1 and row['file_access_type'] == 5 and row['file_destination_type'] == 2:
        if row['manager_presence'] == 1 or row['director_presence'] == 1:
            return 1

    # Administrative Staff move non-confidential and confidential files to external storages with permission from Director.
    if row['computer_user_role'] == 1 and row['file_access_type'] == 4 and row['file_destination_type'] == 2:
        if row['director_presence'] == 1:
            return 1

    # UNAUTHORIZED
    # Administrative Staff copy non-confidential and confidential files to external storages without permission from Manager or Director.
    if row['computer_user_role'] == 1 and row['file_access_type'] == 5 and row['file_destination_type'] == 2:
        if row['manager_presence'] == 0 and row['director_presence'] == 0:
            return 0

    # Administrative Staff move non-confidential and confidential files to external storages without permission from Director.
    if row['computer_user_role'] == 1 and row['file_access_type'] == 4 and row['file_destination_type'] == 2:
        if row['director_presence'] == 0:
            return 0

    # Managers move non-confidential or confidential files to external storages without permission from the Director.
    if row['computer_user_role'] == 2 and row['file_access_type'] == 4 and row['file_destination_type'] == 2:
        if row['director_presence'] == 0:
            return 0


    # SCENARIO 4: Moving/copying files to internal storages
    # AUTHORIZED
    # Directors copy and move both non-confidential and confidential files to internal storages (Self, Manager, Staff)
    if row['computer_user_role'] == 3 and row['file_access_type'] in [4, 5] and row['file_destination_type'] in [1, 3]:
        return 1

    # Managers copy both confidential and non-confidential files to internal storages (Self ,Staff) without permission from the Director
    if row['computer_user_role'] == 2 and row['file_access_type'] == 5 and row['file_destination_type'] in [1, 3]:
        return 1

    # Managers move both confidential and non-confidential files to internal storages (Self, Staff) with permission from the Director
    if row['computer_user_role'] == 2 and row['file_access_type'] == 4 and row['file_destination_type'] in [1, 3]:
        if row['director_presence'] == 1:
            return 1

    # Administrative Staff copy non-confidential files to internal storage (self) without permission from the Manager or Director
    if row['computer_user_role'] == 1 and row['file_access_type'] == 5 and row['file_destination_type'] == 1 and row[
        'is_confidential'] == 0:
            return 1

    # Administrative Staff move non-confidential files to internal storage (self) with permission from the Manager or Director
    if row['computer_user_role'] == 1 and row['file_access_type'] == 4 and row['file_destination_type'] == 1 and row[
        'is_confidential'] == 0:
        if row['manager_presence'] == 1 or row['director_presence'] == 1:
            return 1

    # Administrative Staff copy confidential files to internal storage (self) of with permission from a Manager or Director
    if row['computer_user_role'] == 1 and row['file_access_type'] == 5 and row['file_destination_type'] == 1 and row[
        'is_confidential'] == 1:
        if row['manager_presence'] == 1 or row['director_presence'] == 1:
            return 1

    # Administrative Staff move confidential files to internal storage (self) of with permission from the Director
    if row['computer_user_role'] == 1 and row['file_access_type'] == 4 and row['file_destination_type'] == 1 and row[
        'is_confidential'] == 1:
        if row['director_presence'] == 1:
            return 1

    # UNAUTHORIZED
    # Administrative Staff move non-confidential files to internal storage (self) of without permission from a Manager or Director
    if row['computer_user_role'] == 1 and row['file_access_type'] == 4 and row['file_destination_type'] == 1 and row[
        'is_confidential'] == 0:
        if row['manager_presence'] == 0 and row['director_presence'] == 0:
            return 0

    # Administrative Staff copy confidential files to internal storage (self) of without permission from a Manager or Director
    if row['computer_user_role'] == 1 and row['file_access_type'] == 5 and row['file_destination_type'] == 1 and row[
        'is_confidential'] == 1:
        if row['manager_presence'] == 0 and row['director_presence'] == 0:
            return 0

    # Administrative Staff move confidential files to internal storage (self) of without permission from the Director
    if row['computer_user_role'] == 1 and row['file_access_type'] == 4 and row['file_destination_type'] == 1 and row[
        'is_confidential'] == 1:
        if row['director_presence'] == 0:
            return 0

    # Managers move both confidential and non-confidential files to internal storages (Self, Staff) without permission from the director
    if row['computer_user_role'] == 2 and row['file_access_type'] == 4 and row['file_destination_type'] in [1, 3]:
        if row['director_presence'] == 0:
            return 0

    # SCENARIO 5: Deleting files
    # AUTHORIZED
    # Directors deleting confidential and non-confidential files
    if row['computer_user_role'] == 3 and row['file_access_type'] == 3:
        return 1

    # Managers and administrative staff deleting confidential and non-confidential files with the permission from the Director
    if row['computer_user_role'] in [1, 2] and row['file_access_type'] == 3:
        if row['director_presence'] == 1:
            return 1

    # UNAUTHORIZED
    # Managers and administrative staff deleting confidential and non-confidential files without the permission from the Director
    if row['computer_user_role'] in [1, 2] and row['file_access_type'] == 3:
        if row['director_presence'] == 0:
            return 0

    # SCENARIO 6: Opening files
    # AUTHORIZED
    # Directors and managers opening confidential and non-confidential files
    if row['computer_user_role'] in [2, 3] and row['file_access_type'] == 1:
        return 1

    # Administrative staff opening non-confidential files without permission from the manager or director.
    if row['computer_user_role'] == 1 and row['file_access_type'] == 1 and row['is_confidential'] == 0:
        return 1

    # Administrative staff opening confidential files with permission from the manager or director.
    if row['computer_user_role'] == 1 and row['file_access_type'] == 1 and row['is_confidential'] == 1:
        if row['manager_presence'] == 1 or row['director_presence'] == 1:
            return 1

    # UNAUTHORIZED
    # Administrative staff opening confidential files without permission from the manager or director
    if row['computer_user_role'] == 1 and row['file_access_type'] == 1 and row['is_confidential'] == 1:
        if row['manager_presence'] == 0 and row['director_presence'] == 0:
            return 0

    # SCENARIO 7: Modifying files
    # AUTHORIZED
    # Directors editing non-confidential and confidential files
    if row['computer_user_role'] == 3 and row['file_access_type'] == 2:
        return 1

    # Managers and Administrative Staff modifying non-confidential files
    if row['computer_user_role'] in [1, 2] and row['file_access_type'] == 2 and row['is_confidential'] == 0:
        return 1

    # Managers and Administrative Staff modifying confidential files with permission of the director
    if row['computer_user_role'] in [1, 2] and row['file_access_type'] == 2 and row['is_confidential'] == 1:
        if row['director_presence'] == 1:
            return 1

    # UNAUTHORIZED
    # Managers and Administrative Staff modifying confidential files without permission of the director
    if row['computer_user_role'] in [1, 2] and row['file_access_type'] == 2 and row['is_confidential'] == 1:
        if row['director_presence'] == 0:
            return 0

    return None

def get_incremented_filename(base_dir, base_name):
    base_path = os.path.join(base_dir, base_name)
    if not os.path.exists(base_path):
        return base_path

    base, ext = os.path.splitext(base_name)
    i = 1
    while True:
        new_name = f"{base}_{i}{ext}"
        new_path = os.path.join(base_dir, new_name)
        if not os.path.exists(new_path):
            return new_path
        i += 1

def summarize_authorization_counts(df):
    col = 'authorized'

    df[col] = pd.to_numeric(df[col], errors='coerce')

    one_count = (df[col] == 1).sum()
    zero_count = (df[col] == 0).sum()
    none_count = df[col].isna().sum()

    logging.info(f"'authorization = 1' count: {one_count}")
    logging.info(f"'authorization = 0' count: {zero_count}")
    logging.info(f"Missing or invalid 'authorization' values: {none_count}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python labeller.py <input_csv_path>")
        sys.exit(1)

    input_csv = sys.argv[1]

    df = pd.read_csv(input_csv)

    df = set_authorized(df)

    df = df.drop(columns=["computer_user_role", "file_destination_type", "file_access_type"])

    output_filename = get_incremented_filename(labelled_directory, "labelledDataset.csv")

    df.to_csv(output_filename, index=False)

    summarize_authorization_counts(df)

