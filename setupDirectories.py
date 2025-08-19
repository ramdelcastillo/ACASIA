import os, json

# Get base dir (where this script is run)
base_dir = os.path.dirname(os.path.abspath(__file__))

# Load relative paths
with open(os.path.join(base_dir, "directoriesSetup.json"), "r") as f:
    relative_paths = json.load(f)

# Convert to absolute paths
absolute_paths = {
    key: os.path.abspath(os.path.join(base_dir, rel_path))
    for key, rel_path in relative_paths.items()
}

# Write to a new file (or overwrite if you want)
output_path = os.path.join(base_dir, "directories.json")
with open(output_path, "w") as f:
    json.dump(absolute_paths, f, indent=4)

# Current script is inside ACASIA-CTTHES3
projectRootDirectory = os.path.dirname(os.path.abspath(__file__))

# Load directories.json from the project root (if needed)
directoriesAccess = os.path.join(projectRootDirectory, "directories.json")

with open(directoriesAccess, "r") as f:
    directoryAccess = json.load(f)

# Get path to data_preprocessing config.json
config_path = directoryAccess["data_preprocessing_config"]

# Load the config.json
with open(config_path, "r") as f:
    config_data = json.load(f)  # This is your config dictionary

# Update the path in the config dictionary
config_data["json_file"] = directoryAccess["data_record_logs"]

# Now resolve the full path for transformed_data.csv
transformed_data_directory = os.path.join(
    directoryAccess["data_sets_for_labelling"],
    "transformed.csv"
)

# Update the transformed_data path in config_data
config_data["transformed_data"] = transformed_data_directory

# Save the updated config back to file
with open(config_path, "w") as f:
    json.dump(config_data, f, indent=4)

