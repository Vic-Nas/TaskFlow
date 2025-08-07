

import pyautogui, time

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
        self.action = None
        self.log = ""
        
        if action == "RCLICK":
            self.action = pyautogui.rightClick
            self.log = "RClicked at"
            self.params = list(map(float, self.params))
            
        elif action == "LCLICK":
            self.action = pyautogui.click
            self.log = "LClicked at"
            self.params = list(map(float, self.params))
            
        elif action == "WAIT":
            self.action = time.sleep
            self.log = "Waited"
            self.params = list(map(float, self.params))
            
        elif action == "KEY":
            self.action = pyautogui.hotkey
            self.log = "Pressed"
            
        elif action == "OPEN":
            self.action = open
            self.log = "Opened"
            
        else:
            raise ValueError("Uknown action:", action)
        
    def run(self):
        for _ in range(self.times):
            self.action(*self.params)
            print(self.log, *self.params)
            
class TaskGroup:
    def __init__(self, filePath):
        self.tasks: list[Task] = []
        self.author: str = ""
        self.title: str = ""
        with open(filePath) as file:
            rows = file.readlines()
            self.title = rows[0][1:-1]
            self.author = rows[1][1:-1]
            rows = list(filter(lambda x: x != "\n" and 
                    not x.startswith("#"), rows))
            self.tasks.extend(list(map(Task, rows)))
    
    def run(self):
        for task in self.tasks:
            task.run()
            