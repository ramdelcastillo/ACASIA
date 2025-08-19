import json
import time
import random
import os
from threading import Lock

class DataRecordModule:
    def __init__(self, inputFilePath, outputFilePath, dictionary, ualFilePath, idleTime=0.5):
        self.inputFilePath = inputFilePath
        self.outputFilePath = outputFilePath
        self.dictionary = dictionary
        self.ualFilePath = ualFilePath
        self.lastProcessedLength = 0
        self.idleTime = idleTime
        self.fileLock = Lock()

    def loadUsersActualLocation(self):
        with self.fileLock:
            try:
                with open(self.ualFilePath, 'r') as file:
                    return json.load(file)
            except (FileNotFoundError, json.JSONDecodeError):
                return {}

    def readNewLogs(self):
        with self.fileLock:
            try:
                with open(self.inputFilePath, 'r') as file:
                    logs = json.load(file)
                    newLogs = logs[self.lastProcessedLength:]
                    self.lastProcessedLength = len(logs)
                    return newLogs
            except (FileNotFoundError, json.JSONDecodeError):
                return []

    def appendToOutput(self, updatedLogs):
        with self.fileLock:
            try:
                with open(self.outputFilePath, 'r') as file:
                    existing_logs = json.load(file)
            except (json.JSONDecodeError, FileNotFoundError):
                existing_logs = []

            existing_logs.extend(updatedLogs)

            with open(self.outputFilePath, 'w') as file:
                json.dump(existing_logs, file, indent=4)

    def processLogs(self, UsersActualLocation):
        newLogs = self.readNewLogs()
        if newLogs:
            updatedLogs = [self.updateLogWithLocationAndUsers(log, UsersActualLocation) for log in newLogs]
            self.appendToOutput(updatedLogs)
            self.idleTime = 0.01
        else:
            self.idleTime = min(self.idleTime + 0.1, 0.5)

    def listen(self):
        while True:
            UsersActualLocation = self.loadUsersActualLocation()
            self.processLogs(UsersActualLocation)
            time.sleep(self.idleTime)

    def updateLogWithLocationAndUsers(self, logEntry, UsersActualLocation):
        computerID = logEntry["ComputerID"]
        username = logEntry["Username"]

        computerRoom = self.dictionary.get(computerID, {}).get('ComputerRoom', '')

        nearbyUsers = UsersActualLocation.get(computerRoom, [])

        userLocation = None
        for room, users in UsersActualLocation.items():
            if username in users:
                userLocation = room
                break

        break_status = logEntry.get("breakStatus")

        if userLocation != computerRoom:
            if break_status in [1, 2]:
                if random.random() < 0.9:
                    userLocation = "Room B"
            elif break_status == 0:
                if random.random() < random.uniform(0.05, 0.10):
                    userLocation = "Room B"

        logEntry["NearbyUsers"] = nearbyUsers
        logEntry["ActualLocationOfUsername"] = userLocation
        logEntry["ComputerRoom"] = computerRoom

        return logEntry


if __name__ == "__main__":
    try:
        dataCollectionDirectory = os.path.dirname(os.path.abspath(__file__))
        baseProjectFolderDirectory = base_dir = os.path.abspath(os.path.join(dataCollectionDirectory, ".."))
        directoriesAccess = os.path.join(baseProjectFolderDirectory, "directories.json")

        with open(directoriesAccess, "r") as f:
            directoryAccess = json.load(f)

        filePath = directoryAccess["logs"]
        outputFilePath = directoryAccess["data_record_logs"]
        dictionary = {
            'Computer D': {'ComputerRoom': 'Room D'},
            'Computer A0': {'ComputerRoom': 'Room A'},
            'Computer A1': {'ComputerRoom': 'Room A'},
            'Computer A2': {'ComputerRoom': 'Room A'},
            'Computer C0': {'ComputerRoom': 'Room C'},
            'Computer C1': {'ComputerRoom': 'Room C'},
            'Computer C2': {'ComputerRoom': 'Room C'},
        }
        ualFilePath = directoryAccess["snap_ual"]

        dataRecordModule = DataRecordModule(filePath, outputFilePath, dictionary, ualFilePath)
        print("DataRecordModule running... Press Ctrl+C to stop.")
        dataRecordModule.listen()

    except KeyboardInterrupt:
        print("\nDataRecordModule stopped.")

