import os
import json
import shutil


def getNextBackupFolder(baseDir):
    i = 1
    while True:
        candidate = os.path.join(baseDir, f"backup_{i}")
        if not os.path.exists(candidate):
            return candidate
        i += 1

def copyPathToBackup(srcPath, backupRoot):
    if not os.path.exists(srcPath):
        print(f"Warning: Source path does not exist: {srcPath}")
        return

    name = os.path.basename(srcPath)
    destPath = os.path.join(backupRoot, name)

    if os.path.isdir(srcPath):
        shutil.copytree(srcPath, destPath)
    else:
        shutil.copy2(srcPath, destPath)

def clearFolderContents(folderPath):
    if not os.path.exists(folderPath):
        print(f"Warning: Folder to clear does not exist: {folderPath}")
        return

    for entry in os.listdir(folderPath):
        entryPath = os.path.join(folderPath, entry)
        try:
            if os.path.isdir(entryPath):
                shutil.rmtree(entryPath)
            else:
                os.remove(entryPath)
        except Exception as e:
            print(f"Error deleting {entryPath}: {e}")

def main():
    baseDir = os.path.dirname(os.path.abspath(__file__))
    jsonPath = os.path.join(baseDir, "directories.json")

    with open(jsonPath, "r") as f:
        relativePaths = json.load(f)

    backupFolder = getNextBackupFolder(baseDir)
    os.makedirs(backupFolder)

    print(f"Created backup folder: {backupFolder}")

    excludeKey = "labeller"

    # Backup all except excluded key
    for key, path in relativePaths.items():
        if key == excludeKey:
            print(f"Skipping backup of excluded key: {key}")
            continue
        print(f"Backing up {key}: {path}")
        copyPathToBackup(path, backupFolder)

    print("Backup completed!")

    # Clear specific folders except excluded
    foldersToClear = [
        relativePaths.get("data_sets_for_labelling"),
        relativePaths.get("data_sets_labelled"),
        relativePaths.get("previous_logs"),
    ]

    for folder in foldersToClear:
        if folder and folder != relativePaths.get(excludeKey):
            print(f"Clearing contents of folder: {folder}")
            clearFolderContents(folder)

    print("Cleanup completed!")


if __name__ == "__main__":
    main()
