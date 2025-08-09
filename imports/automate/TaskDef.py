

import pyautogui, time
from collections import defaultdict

matchAction = defaultdict(lambda *args: None)

import os, platform, subprocess

def openFile(path):
    if platform.system() == 'Windows':
        os.startfile(path)
    elif platform.system() == 'Darwin':
        subprocess.run(['open', path])
    else:
        subprocess.run(['xdg-open', path])


matchAction.update({
    "RCLICK": pyautogui.rightClick,
    "LCLICK": pyautogui.click,
    "WAIT": time.sleep,
    "KEY": pyautogui.hotkey,
    "OPEN": lambda filePath: openFile(filePath.replace("[SPACE]", " ")),
    "TYPE": lambda *args: pyautogui.write(",".join(args).replace("[SPACE]", " ")),
    "EXEC": lambda filePath: TaskGroup(filePath.replace("[SPACE]", " ")).run()
    })

class Task:
    def __init__(self, command_line: str):
        self._extra = {}  # internal dict-like storage

        parts = command_line.split("  ")
        if len(parts) != 4:
            print("Not enough parts:", command_line)
            parts = ["None", "", "0", "Do Nothing"]

        action, params, times, desc = parts
        self.params = params.split(" ")
        self.times = int(times)
        self.desc = desc
        self.action = matchAction[action]
        self.log = ""
                
        if action == "RCLICK":
            self.log = "RClicked at"
            self.params = list(map(float, self.params))
        elif action == "LCLICK":
            self.log = "LClicked at"
            self.params = list(map(float, self.params))
        elif action == "WAIT":
            self.log = "Waited"
            self.params = list(map(float, self.params))
        elif action == "KEY":
            self.log = "Pressed"
        elif action == "OPEN":
            self.log = "Opened"
        elif action == "TYPE":
            self.log = "Typed"
        elif action == "EXEC":
            self.log = "Ran"
        else:
            raise ValueError(f"Unknown action: {action}")

    # --- dict-like access for extra data ---
    def __getitem__(self, key):
        return self._extra.get(key, None)  # default None

    def __setitem__(self, key, value):
        self._extra[key] = value

    def __delitem__(self, key):
        if key in self._extra:
            del self._extra[key]

    def __contains__(self, key):
        return key in self._extra

    def update(self, other: dict):
        """Update internal dict-like storage with another dict."""
        self._extra.update(other)

        
    def run(self):
        for _ in range(self.times):
            self.action(*self.params)
            print(self.log, *self.params)
            
    def __str__(self):
        action = ""
        for name, func in matchAction.items():
            if func == self.action:
                action = name
                break
        
        parts = [
            action, " ".join(list(map(str, self.params))),
            str(self.times), self.desc
        ]
        
        return "  ".join(parts)
    
    def update(self, other = None):
        if other is None:
            return
        if isinstance(other, dict):
            self._extra.update(other)
        elif isinstance(other, Task):
            self._extra.update(other._extra)
        else:
            raise TypeError("update() accepts a dict or Task instance")



            
class TaskGroup:
    def __init__(self, filePath = "", author = "", title = "", maxTasks = 14):
        self.tasks: list[Task] = []
        self.author: str = author
        self.title: str = title
        self.maxTasks = maxTasks
        try:
            with open(filePath) as file:
                rows = file.readlines()
                if not self.title:
                    self.title = rows[0][1:-1]
                if not self.author:
                    self.author = rows[1][1:-1]
                rows = list(filter(lambda x: x != "\n" and 
                        not x.startswith("#"), rows))
                self.tasks.extend(list(map(Task, rows[:self.maxTasks])))
        except Exception as e:
            print(e)
    
    def run(self):
        for task in self.tasks:
            task.run()
            
    def saveAt(self, targetPath):
        with open(targetPath, 'w') as file:
            file.write(f"#{self.title}\n")
            file.write(f"#{self.author}\n")
            file.write("#ACTION  PARAMS  TIMES  Desc\n")
            file.write("\n")
            
            for task in self.tasks:
                file.write(str(task) + "\n")
                
    def insert(self, index: int, task: Task):
        if len(self.tasks) >= self.maxTasks:
            raise IndexError("Maximum index of tasks reach.")
        else: self.tasks.insert(index, task)
