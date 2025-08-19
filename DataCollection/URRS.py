import tkinter as tk
import json
import os
from random import randint
import time
import threading
import random
from filelock import FileLock, Timeout

dataCollectionDirectory = os.path.dirname(os.path.abspath(__file__))
baseProjectFolderDirectory = base_dir = os.path.abspath(os.path.join(dataCollectionDirectory, ".."))
directoriesAccess = os.path.join(baseProjectFolderDirectory, "directories.json")

with open(directoriesAccess, "r") as f:
    directoryAccess = json.load(f)

UAL_FILE_PATH = directoryAccess["ual"]
SNAP_UAL_FILE_PATH = directoryAccess["snap_ual"]

class User:
    def __init__(self, name, position=(0, 0)):
        self.name = name
        self.position = position

class Model:
    def __init__(self):
        self.users = []

    def addUser(self, user):
        self.users.append(user)

    def getUserByName(self, username):
        for user in self.users:
            if user.name == username:
                return user
        return None

class View(tk.Tk):
    def __init__(self, windowSize=900, squareSize=600):
        super().__init__()
        self.controller = None
        self.windowSize = windowSize
        self.squareSize = squareSize
        self.geometry(f"{self.windowSize}x{self.windowSize}")
        self.json_lock = threading.Lock()

        # Create a navbar frame at the top
        self.navbar = tk.Frame(self, bg="lightgray", height=50)
        self.navbar.pack(side="top", fill="x")

        # Add Start Simulation button inside the navbar
        self.start_sim_button = tk.Button(self.navbar, text="Start Simulation",
                                          command=lambda: self.controller.startUserMovement())
        self.start_sim_button.pack(pady=10, padx=10, side="left")

        # Add Stop Simulation button inside the navbar
        self.stop_sim_button = tk.Button(self.navbar, text="Stop Simulation",
                                         command=lambda: self.controller.stopUserMovement())
        self.stop_sim_button.pack(pady=10, padx=10, side="left")

        # Canvas for main content
        self.canvas = tk.Canvas(self, width=self.windowSize, height=self.windowSize, bg="white")
        self.canvas.pack(fill="both", expand=True)

        self.drawQuadrants()
        self.userCircles = {}
        self.userTexts = {}
        self.currentlyDragging = None
        self.offsetX = 0
        self.offsetY = 0

    def getRandomPositionForRoom(self, room_name, spread=False):
        basePositions = {
            "Room A": (300 * 0.65, 600 * 0.65),
            "Room C": (250 * 0.65, 250 * 0.65),
            "Room D": (600 * 0.65, 250 * 0.65),
            "Room B": (600 * 0.65, 550 * 0.65)
        }

        if room_name in basePositions:
            baseX, baseY = basePositions[room_name]

            if spread:
                offsetX = random.randint(-70, 70)
                offsetY = random.randint(-70, 70)
                return (int(baseX + offsetX), int(baseY + offsetY))

            return (int(baseX), int(baseY))

        return None

    def getShortName(self, fullName):
        return "".join([word[0] for word in fullName.split()]) + fullName[-1] if fullName else fullName

    def setController(self, controller):
        self.controller = controller

    def drawQuadrants(self):
        self.squareSize = min(self.squareSize, self.windowSize)
        offset = (self.windowSize - self.squareSize) // 2

        self.canvas.create_rectangle(
            offset, offset,
            offset + self.squareSize, offset + self.squareSize,
            outline="black", width=2
        )

        midX = offset + self.squareSize / 2
        midY = offset + self.squareSize / 2

        self.canvas.create_line(midX, offset, midX, offset + self.squareSize, fill="black", width=2)
        self.canvas.create_line(offset, midY, offset + self.squareSize, midY, fill="black", width=2)

        self.canvas.create_text(offset + self.squareSize * 0.25, offset + self.squareSize * 0.25, text="Room C",
                                font=("Arial", 16))
        self.canvas.create_text(offset + self.squareSize * 0.75, offset + self.squareSize * 0.25, text="Room D",
                                font=("Arial", 16))
        self.canvas.create_text(offset + self.squareSize * 0.25, offset + self.squareSize * 0.75, text="Room A",
                                font=("Arial", 16))
        self.canvas.create_text(offset + self.squareSize * 0.75, offset + self.squareSize * 0.75, text="Room B",
                                font=("Arial", 16))

    def drawUserCircle(self, user):
        x, y = user.position
        circle = self.canvas.create_oval(x - 25, y - 25, x + 25, y + 25, fill="blue", outline="")
        shortName = self.getShortName(user.name)
        nameText = self.canvas.create_text(x, y, text=shortName, fill="white", font=("Arial", 12))

        self.userCircles[user.name] = circle
        self.userTexts[user.name] = nameText

        self.canvas.tag_bind(circle, "<Button-1>", lambda event, user=user: self.startDrag(event, user))
        self.canvas.tag_bind(circle, "<B1-Motion>", lambda event, user=user: self.drag(event, user))
        self.canvas.tag_bind(circle, "<ButtonRelease-1>", lambda event, user=user: self.stopDrag(event, user))

    def checkRoom(self, user):
        x, y = user.position
        offset = (self.windowSize - self.squareSize) // 2
        midX = offset + self.squareSize / 2
        midY = offset + self.squareSize / 2

        if not (offset <= x <= offset + self.squareSize and offset <= y <= offset + self.squareSize):
            return "Outside the rooms"

        if x < midX and y < midY:
            return "Room C"
        elif x < midX and y > midY:
            return "Room A"
        elif x > midX and y < midY:
            return "Room D"
        elif x > midX and y > midY:
            return "Room B"

    def updateUalJson(self, user, room):
        with self.json_lock:
            try:
                with open(UAL_FILE_PATH, "r") as file:
                    roomAssignments = json.load(file)
            except FileNotFoundError:
                roomAssignments = {"Room A": [], "Room B": [], "Room C": [], "Room D": []}

            for key in roomAssignments:
                if user.name in roomAssignments[key]:
                    roomAssignments[key].remove(user.name)

            if room != "Outside the rooms" and user.name not in roomAssignments[room]:
                roomAssignments[room].append(user.name)

            with open(UAL_FILE_PATH, "w") as file:
                json.dump(roomAssignments, file, indent=4)

    def startDrag(self, event, user):
        self.currentlyDragging = user
        self.offsetX = self.canvas.coords(self.userCircles[user.name])[0] - event.x
        self.offsetY = self.canvas.coords(self.userCircles[user.name])[1] - event.y

    def drag(self, event, user):
        if self.currentlyDragging == user:
            x1 = event.x + self.offsetX
            y1 = event.y + self.offsetY
            x2 = x1 + 50
            y2 = y1 + 50
            self.canvas.coords(self.userCircles[user.name], x1, y1, x2, y2)
            self.canvas.coords(self.userTexts[user.name], x1 + 25, y1 + 25)
            user.position = (x1 + 25, y1 + 25)

    def stopDrag(self, event, user):
        if self.currentlyDragging == user:
            self.currentlyDragging = None
            room = self.checkRoom(user)
            self.updateUalJson(user, room)


class Controller:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.view.setController(self)
        self.roomCounts = {}
        self.stopThreads = {}
        self.loadUsersFromJson()
        self.lock = threading.Lock()
        self.breakLock = FileLock(directoryAccess["break_tracker"] + ".lock")
        self.userStatusList = {
            "AS1": 0,
            "AS2": 0,
            "AS3": 0,
            "AS4": 0,
            "Manager1": 0,
            "AS5": 0,
            "AS6": 0,
            "AS7": 0,
            "AS8": 0,
            "Manager2": 0,
            "Director1": 0
        }

        threading.Thread(target=self.monitorBreakTracker, daemon=True).start()

    def monitorBreakTracker(self):
        while True:
            try:
                with self.breakLock.acquire(timeout=1):
                    with open(directoryAccess["break_tracker"], "r") as f:
                        data = json.load(f)
                        for key in self.userStatusList:
                            if key in data:
                                self.userStatusList[key] = data[key]
            except (json.JSONDecodeError, FileNotFoundError, Timeout):
                pass
            time.sleep(0.6)

    def startUserMovement(self):
        """Starts threads that move all predefined users between rooms at intervals."""
        users = ["AS1", "AS2", "AS3", "AS4", "AS5", "AS6", "AS7", "AS8", "Manager1", "Manager2", "Director1"]
        # users = ["AS1"]

        for username in users:
            if username in self.stopThreads:
                # print(f"User {username} is already moving.")
                continue

            user = self.model.getUserByName(username)  # Assuming this retrieves the user object
            if not user:
                # print(f"User {username} not found!")
                continue

            stopEvent = threading.Event()
            self.stopThreads[username] = stopEvent
            thread = threading.Thread(target=self.simulateUserMovement, args=(user, stopEvent))
            thread.daemon = True
            thread.start()
            print(f"Started movement for {username}")

    def stopUserMovement(self, username=None):
        """Stops movement for a specific user or all users if no username is provided."""
        if username:
            if username in self.stopThreads:
                self.stopThreads[username].set()
                del self.stopThreads[username]
                print(f"Stopped movement for {username}")
        else:
            for user in list(self.stopThreads.keys()):
                self.stopThreads[user].set()
                del self.stopThreads[user]
                print(f"Stopped movement for {user}")

    def loadUsersFromJson(self):
        try:
            with open(UAL_FILE_PATH, "r") as file:
                roomAssignments = json.load(file)

            for room, users in roomAssignments.items():
                for username in users:
                    user = User(
                        name=username,
                        position=self.getInitialPositionForRoom(room)
                    )
                    self.model.addUser(user)
                    self.view.drawUserCircle(user)

        except (FileNotFoundError, json.JSONDecodeError):
            print("Error loading ual.json, proceeding with no users.")

    def simulateUserMovement(self, user, stopEvent):
        rooms = ["Room A", "Room B", "Room C", "Room D"]

        allUsersUsernames = ["AS1", "AS2", "AS5", "AS6", "AS3", "AS4", "AS7", "AS8", "Manager1", "Manager2", "Director1"]
        ASRoomAUsernames = ["AS1", "AS2", "AS5", "AS6"]
        ASRoomCUsernames = ["AS3", "AS4", "AS7", "AS8"]
        managersUsernames = ["Manager1", "Manager2"]
        directorUsername = "Director1"

        ASRoomAUsernamesNotOnBreakRooms = [1, 2, 3, 0]
        ASRoomCUsernamesNotOnBreakRooms = [1, 0, 3, 2]
        managersUsernamesNotOnBreakRooms = [1, 3, 0, 2]
        directorUsernameNotOnBreakRooms = [1, 2, 0, 3]

        ASRoomAUsernamesOnBreakOrOutOfShiftRooms = [2, 3, 0, 1]
        ASRoomCUsernamesOnBreakOrOutOfShiftRooms = [0, 3, 2, 1]
        managersUsernamesOnBreakOrOutOfShiftRooms = [0, 3, 2, 1]
        directorUsernameOnBreakOrOutOfShiftRooms = [2, 0, 3, 1]

        delayForMoreSeconds = 0

        while not stopEvent.is_set():
            userStatus = self.userStatusList[user.name]
            if user.name in allUsersUsernames and userStatus == 0: # NORMAL WORKING HOURS
                if user.name in ASRoomAUsernames:
                    # ASRoomAUsernames = ["AS1", "AS2", "AS5", "AS6"]
                    # ASRoomAUsernamesNotOnBreakRooms = [1, 2, 3, 0]
                    newRoom = random.choices(ASRoomAUsernamesNotOnBreakRooms, weights=[0.02, 0.10, 0.04, 0.84], k=1)[0]
                if user.name in ASRoomCUsernames:
                    # ASRoomCUsernames = ["AS3", "AS4", "AS7", "AS8"]
                    # ASRoomCUsernamesNotOnBreakRooms =  [1, 0, 3, 2]
                    newRoom = random.choices(ASRoomCUsernamesNotOnBreakRooms, weights=[0.02, 0.10, 0.04, 0.84], k=1)[0]
                if user.name in managersUsernames:
                    # managersUsernames = ["Manager1", "Manager2"]
                    # managersUsernamesNotOnBreakRooms = [1, 3, 0, 2]
                    newRoom = random.choices(managersUsernamesNotOnBreakRooms, weights=[0.02, 0.20, 0.39, 0.39], k=1)[0]
                    if newRoom in [0, 2]:
                        delayForMoreSeconds = randint(48, 96) * 1.2
                if user.name == directorUsername:
                    # directorUsername = "Director1"
                    # directorUsernameNotOnBreakRooms = [1, 2, 0, 3]
                    newRoom = random.choices(directorUsernameNotOnBreakRooms, weights=[0.02, 0.05, 0.05, 0.88], k=1)[0]
                    if newRoom in [0, 2]:
                        delayForMoreSeconds = randint(12, 24) * 1.2
            if user.name in allUsersUsernames and userStatus == 1: # BREAK HOURS
                if user.name in ASRoomAUsernames:
                    # ASRoomAUsernames = ["AS1", "AS2", "AS5", "AS6"]
                    # ASRoomAUsernamesOnBreakOrOutOfShiftRooms = [2, 3, 0, 1]
                    newRoom = random.choices(ASRoomAUsernamesOnBreakOrOutOfShiftRooms, weights=[0.03, 0.02, 0.15, 0.80], k=1)[0]
                if user.name in ASRoomCUsernames:
                    # ASRoomCUsernames = ["AS3", "AS4", "AS7", "AS8"]
                    # ASRoomCUsernamesOnBreakOrOutOfShiftRooms = [0, 3, 2, 1]
                    newRoom = random.choices(ASRoomCUsernamesOnBreakOrOutOfShiftRooms, weights=[0.03, 0.02, 0.15, 0.80], k=1)[0]
                if user.name in managersUsernames:
                    # managersUsernames = ["Manager1", "Manager2"]
                    # managersUsernamesOnBreakOrOutOfShiftRooms = [0, 3, 2, 1]
                    newRoom = random.choices(managersUsernamesOnBreakOrOutOfShiftRooms, weights=[0.09, 0.02, 0.09, 0.80], k=1)[0]
                if user.name == directorUsername:
                    # directorUsername = "Director1"
                    # directorUsernameOnBreakOrOutOfShiftRooms = [2, 0, 3, 1]
                    newRoom = random.choices(directorUsernameOnBreakOrOutOfShiftRooms, weights=[0.01, 0.01, 0.11, 0.87], k=1)[0]
                delayForMoreSeconds = randint(3, 8) * 1.2  # TO GIVE ENOUGH TIME FOR R00M MISMATCH
            if user.name in allUsersUsernames and userStatus == 2:
                # 0.05 Chance to simulate out of shift time actions
                if user.name in ASRoomAUsernames:
                    # ASRoomAUsernames = ["AS1", "AS2", "AS5", "AS6"]
                    # ASRoomAUsernamesOnBreakOrOutOfShiftRooms = [2, 3, 0, 1]
                    newRoom = random.choices(ASRoomAUsernamesOnBreakOrOutOfShiftRooms, weights=[0.01, 0.01, 0.02, 0.96], k=1)[0]
                if user.name in ASRoomCUsernames:
                    # ASRoomCUsernames = ["AS3", "AS4", "AS7", "AS8"]
                    # ASRoomCUsernamesOnBreakOrOutOfShiftRooms = [0, 3, 2, 1]
                    newRoom = random.choices(ASRoomCUsernamesOnBreakOrOutOfShiftRooms, weights=[0.01, 0.01, 0.02, 0.96], k=1)[0]
                if user.name in managersUsernames:
                    # managersUsernames = ["Manager1", "Manager2"]
                    # managersUsernamesOnBreakOrOutOfShiftRooms = [0, 3, 2, 1]
                    newRoom = random.choices(managersUsernamesOnBreakOrOutOfShiftRooms, weights=[0.02, 0.01, 0.02, 0.95], k=1)[0]
                if user.name == directorUsername:
                    # directorUsername = "Director1"
                    # directorUsernameOnBreakOrOutOfShiftRooms = [2, 0, 3, 1]
                    newRoom = random.choices(directorUsernameOnBreakOrOutOfShiftRooms, weights=[0.01, 0.01, 0.02, 0.96], k=1)[0]
                delayForMoreSeconds = randint(3, 8) * 1.2 # TO GIVE ENOUGH TIME FOR OUT OF SHIFT ACCESS


            newPosition = self.view.getRandomPositionForRoom(rooms[newRoom], spread=True)

            if newPosition:
                user.position = newPosition
                self.view.canvas.coords(
                    self.view.userCircles[user.name],
                    newPosition[0] - 25, newPosition[1] - 25,
                    newPosition[0] + 25, newPosition[1] + 25
                )
                self.view.canvas.coords(
                    self.view.userTexts[user.name],
                    newPosition[0], newPosition[1]
                )

                self.view.updateUalJson(user, rooms[newRoom])

            time.sleep(1.2 + delayForMoreSeconds)
            delayForMoreSeconds = 0

    def getInitialPositionForRoom(self, room):
        base_positions = {
            "Room A": (300 * 0.65, 600 * 0.65),
            "Room C": (250 * 0.65, 250 * 0.65),
            "Room D": (600 * 0.65, 250 * 0.65),
            "Room B": (600 * 0.65, 550 * 0.65)
        }

        baseX, baseY = base_positions.get(room, (0, 0))
        count = self.roomCounts.get(room, 0)

        offsetX = (count % 3) * 30
        offsetY = (count // 3) * 30

        newPosition = (baseX + offsetX, baseY + offsetY)

        self.roomCounts[room] = count + 1

        return newPosition


if __name__ == "__main__":
    model = Model()
    view = View(windowSize=585, squareSize=390)
    controller = Controller(model, view)
    view.mainloop()