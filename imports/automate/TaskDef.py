

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
    "OPEN": lambda path: openFile(path.replace("[SPACE]", " ")),
    "TYPE": lambda *args: pyautogui.write(",".join(args).replace("[SPACE]", " "))
    })

class Task:
    def __init__(self, commandLine: str):
        split = commandLine.split("  ")
        if len(split) != 4:
            print("Not enough parts:", commandLine)
            split = ["None", "", "0", "Do Nothing"]
        action, params, times, desc = split
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
            
        else:
            raise ValueError(f"Uknown action: {action}")
        
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
    
    def update(self, other):
        for k, v in other.__dict__.items():
            if k not in []:  # Blacklist
                setattr(self, k, v)

            
class TaskGroup:
    def __init__(self, filePath = "", author = "", title = ""):
        self.tasks: list[Task] = []
        self.author: str = author
        self.title: str = title
        try:
            with open(filePath) as file:
                rows = file.readlines()
                if not self.title:
                    self.title = rows[0][1:-1]
                if not self.author:
                    self.author = rows[1][1:-1]
                rows = list(filter(lambda x: x != "\n" and 
                        not x.startswith("#"), rows))
                self.tasks.extend(list(map(Task, rows)))
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
