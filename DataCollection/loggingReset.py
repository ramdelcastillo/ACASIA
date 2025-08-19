import json
import shutil
import os

dataCollectionDirectory = os.path.dirname(os.path.abspath(__file__))
baseProjectFolderDirectory = baseDir = os.path.abspath(os.path.join(dataCollectionDirectory, ".."))
directoriesAccessPath = os.path.join(baseProjectFolderDirectory, "directories.json")

with open(directoriesAccessPath, "r") as f:
    directoryAccess = json.load(f)

loggingJson = directoryAccess["logging"]
loggingReset = directoryAccess["logging_reset"]
logsJson = directoryAccess["logs"]
dataRecordLogs = directoryAccess["data_record_logs"]
breakTracker = directoryAccess["break_tracker"]
breakTrackerReset = directoryAccess["break_tracker_reset"]

shutil.copyfile(loggingReset, loggingJson)

for filePath in [logsJson, dataRecordLogs]:
    with open(filePath, "w") as f:
        json.dump([], f, indent=4)

shutil.copyfile(breakTrackerReset, breakTracker)

print("Reset completed.")
