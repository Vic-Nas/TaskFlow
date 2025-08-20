

import pyautogui
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
        
        
import tkinter as tk
import time

import tkinter as tk
import time

import tkinter as tk
import time

def wait(seconds, display=True, description="Waiting", color="red", size=120, parent=None):
    """Visual countdown with big floating numbers"""
    
    if not display:
        time.sleep(seconds)
        return
    
    # Handle float seconds
    isFloat = isinstance(seconds, float)
    totalSeconds = seconds
    wholeSeconds = int(seconds)
    
    # Get parent window - don't create new root or modify existing one
    if parent is None:
        parent = tk._default_root
        if parent is None:
            # This shouldn't happen in a proper tkinter app
            raise RuntimeError("No parent window available and no default root exists")
    
    # Create countdown window
    countdownWindow = tk.Toplevel(parent)
    countdownWindow.overrideredirect(True)  # Remove window decorations
    countdownWindow.attributes('-topmost', True)  # Always visible
    
    # Try to set transparent color (may not work on all systems)
    try:
        countdownWindow.attributes('-transparentcolor', 'black')
        bg_color = 'black'
    except tk.TclError:
        # Fallback if transparency not supported
        bg_color = '#000001'  # Almost black
        countdownWindow.attributes('-alpha', 0.8)  # Semi-transparent
    
    # Window size adapted to font size
    windowWidth = int(size * 3.5)
    windowHeight = int(size * 3)  # Slightly taller for description
    
    # Center window on screen
    screenWidth = countdownWindow.winfo_screenwidth()
    screenHeight = countdownWindow.winfo_screenheight()
    posX = (screenWidth - windowWidth) // 2
    posY = (screenHeight - windowHeight) // 2
    countdownWindow.geometry(f"{windowWidth}x{windowHeight}+{posX}+{posY}")
    
    # Background
    countdownWindow.configure(bg=bg_color)
    
    # Description label
    descLabel = tk.Label(countdownWindow,
                        text=description,
                        font=("Arial", max(12, size // 6), "normal"),
                        fg=color,
                        bg=bg_color)
    descLabel.pack(pady=(20, 5))
    
    # Label for the countdown number
    numberLabel = tk.Label(countdownWindow, 
                          text="", 
                          font=("Arial", size, "bold"), 
                          fg=color, 
                          bg=bg_color)
    numberLabel.pack(expand=True)
    
    # Force initial display
    countdownWindow.update_idletasks()
    countdownWindow.update()
    
    # Display countdown using after() instead of time.sleep()
    def countdown(remaining):
        if remaining > 0:
            if remaining <= wholeSeconds:  # Only show whole numbers
                numberLabel.config(text=str(int(remaining)))
                countdownWindow.update_idletasks()
            
            # Schedule next update
            if remaining > 1:
                countdownWindow.after(1000, lambda: countdown(remaining - 1))
            else:
                # Handle final fractional second
                if isFloat:
                    finalDelay = int((remaining % 1) * 1000)
                    if finalDelay > 0:
                        countdownWindow.after(finalDelay, countdownWindow.destroy)
                    else:
                        countdownWindow.destroy()
                else:
                    countdownWindow.after(1000, countdownWindow.destroy)
        else:
            countdownWindow.destroy()
    
    # Start countdown
    if wholeSeconds > 0:
        countdown(totalSeconds)
    else:
        # Just fractional seconds
        delay = int(totalSeconds * 1000)
        countdownWindow.after(delay, countdownWindow.destroy)
    
    # Wait for countdown to complete
    parent.wait_window(countdownWindow)



matchAction.update({
    "RCLICK": pyautogui.rightClick,
    "LCLICK": pyautogui.click,
    "WAIT": wait,
    "KEY": pyautogui.hotkey,
    "OPEN": lambda filePath: openFile(filePath.replace("[SPACE]", " ")),
    "TYPE": lambda *args: pyautogui.write(",".join(args).replace("[SPACE]", " ")),
    "EXEC": lambda filePath: TaskGroup(filePath.replace("[SPACE]", " ")).run()
    })

class Task:
    def __init__(self, command_line: str):
        self._extra = {}  # internal dict-like storage
        self.log = ""

        parts = command_line.split("  ")
        if len(parts) != 4:
            print("Not enough parts:", command_line)
            parts = ["None", "", "0", "Do Nothing"]

        action, params, times, desc = parts
        self.params = params.split(" ")
        self.times = int(times)
        self.desc = desc
        self.action = matchAction[action]
                
        if action == "RCLICK":
            self.params = list(map(float, self.params))
            self.log = "Rclicked at"
        elif action == "LCLICK":
            self.params = list(map(float, self.params))
            self.log = "Lclicked at"
        elif action == "WAIT":
            self.params[0] = float(self.params[0])
            if len(self.params) == 2: 
                if self.params[1] in ["False", "0"]:
                    self.params[1] = False
                else:
                    self.params[1] = True
            # Add description parameter for wait function
            self.params.append(self.desc)
            self.log = "Waited"
        elif action == "KEY":
            self.log = "Pressed"
        elif action == "OPEN":
            self.log = "Opened"
        elif action == "TYPE":
            self.log = "Typed"
        elif action == "EXEC":
            self.log = "Executed"
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


    def clear(self):
        """Empty internal dict-like storage."""
        self._extra.clear()

        
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
    
    def update(self, other, updateExtra = True):
        if isinstance(other, Task):
            # Copy core attributes
            self.params = other.params
            self.times = other.times
            self.desc = other.desc
            self.action = other.action
            self.log = other.log

            # Optionally merge _extra
            if updateExtra:
                self._extra.update(other._extra)

        elif isinstance(other, dict):
            self._extra.update(other)
        else:
            raise TypeError("update() expects a Task or dict")


            
class TaskGroup:
    def __init__(self, filePath = "", author = "", title = "", maxTasks = 1000):
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
