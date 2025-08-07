
from imports.settings import logged, login, color, getSetting
from imports.utils import centerWin
import webbrowser
from pathlib import Path
from imports.automate.TaskDef import TaskGroup, matchAction, Task
from tkinter import filedialog
from shutil import copy, copy2
from imports.automate.detectCoords import SimpleCircleOverlay

from pymsgbox import alert, prompt
import tkinter, sys

import os

overlay = None

def reload():
    print(color("Reloading window", "cyan"))
    root.destroy()
    main()

def main():
    global root, overlay
    filePaths = {}
    widgets = {}
    tasksDir = "tasks"
    taskGroups: list[TaskGroup] = []

    if not logged():
        try:
            login()
        except Exception as e:
            print("Login error:", e)
        
    if not logged():
        alert("You must log in")
        sys.exit()
        
    root = tkinter.Tk()
    root.geometry("1200x800")
    root.resizable(False, False)
    root.iconbitmap(Path("data")/"logo.ico")
    root.title("TaskFlow")
    centerWin(root)
    fontStyle = "Times New Roman"


    def onClick(buttonText, ref = None):
        global selectedGroup
        match buttonText:
            case "☕ Buy me a coffee":
                webbrowser.open("https://coff.ee/vicnas")
                print("Buying coffee")
            case "Select Group":
                for widget in chosenGroupFrame.winfo_children():
                    widget.destroy()
                selectedGroup = taskGroups[tasksListBox.curselection()[0]]
                displaySelected()
                print(color("Displaying", "green"), selectedGroup.title)
            case "Import Group":
                filePath = filedialog.askopenfilename(
                title = "Choose .task file",
                filetypes = [("Task file", "*.task")]
                )
                print(color("Chose to open file:", "blue"), 
                    filePath if filePath else None)
                
                if filePath:
                    copy(filePath, Path("tasks"))
                    reload()
                    
            case "Run Group":
                for task in selectedGroup.tasks:
                    widgets[task]["run"].invoke()
                    
            case "New Group":
                title = prompt("Group name: ")
                group = TaskGroup(title = title, 
                                  author = getSetting("email")
                                  )
                group.saveAt(Path("tasks")/f"{group.title}.task")
                reload()
                
            case "DoubleClick Group":
                os.remove(filePaths[selectedGroup])
                reload()
                
            case "Detect Coords":
                if overlay:
                    overlay.close_app()
                overlay = SimpleCircleOverlay()
                overlay.run()
                
                    
            case "❌":
                task = widgets[ref]["task"]
                selectedGroup.tasks.remove(task)
                selectedGroup.saveAt(filePaths[selectedGroup])
                onClick("Select Group")
                    
            case "Add Task":
                newTask = Task("WAIT  1  1  No description")
                selectedGroup.tasks.append(newTask)
                selectedGroup.saveAt(filePaths[selectedGroup])
                onClick("Select Group")
                
                    
            case "Run":
                try:
                    widgets[widgets[ref]["task"]]["save"].invoke()
                    widgets[ref]["task"].run()
                    
                except Exception as e:
                    print(e)
                    alert("Can't run that task.")
                
            case "Save":
                try:
                    params = " ".join(widgets[ref]["args"].get().replace(" ", "[SPACE]").split(","))
                    command = widgets[ref]["command"].get()
                    desc = widgets[ref]["desc"].get()
                    times = widgets[ref]["times"].get()
                    newTask = Task("  ".join(
                        [command, params, times, desc]
                    ))
                    widgets[ref]["task"].update(newTask)
                    selectedGroup.saveAt(filePaths[selectedGroup])
            
                except Exception as e:
                    alert("Error in Task")
                    print(e)
            
            
            case "Share":
                folder_path = filedialog.askdirectory(
                title = "Select folder to save task file",
                initialdir = "."  # Current folder as default
            )
            
                if folder_path:  # If user didn't cancel
                    try:
                        # Complete destination path
                        destination = os.path.join(folder_path, f"{selectedGroup.title.replace(" ", "_")}.task")
                        
                        # Copy task file to chosen folder
                        copy2(filePaths[selectedGroup], destination)
                        print(f"Task file saved to: {destination}")
                        
                    except FileNotFoundError:
                        print("Error: task.task file not found")
                    except Exception as e:
                        print(f"Error saving file: {e}")
                else:
                    print("Save cancelled")
                
            case _:  # default case
                print(color(buttonText, "red"), "clicked.")
                alert("Unavailable for now.")

    class MyButton(tkinter.Button):
        def __init__(self, master, **kwargs):
            super().__init__(master, **kwargs)
            
            self.config(
                command = lambda: onClick(self['text'], 
                                            ref = self))
            
            
    # High Frame: 5 buttons
    highFrameBg = "violet"
    highFrame = tkinter.Frame(root, bg = highFrameBg, width = 1200, 
                            height = 60
                            )
    highFrame.pack()
    highFrame.grid_propagate(False)

    taskFlowButton = MyButton(highFrame, text = "TaskFlow", borderwidth = 0,
                                    font = (fontStyle, 20, "bold"), 
                                    bg = highFrameBg, fg = "white",
                                    )

    taskFlowButton.grid(row = 0, column = 0, pady = 5)

    userLabel = tkinter.Label(highFrame, text = getSetting("email"), 
                            font = (fontStyle, 20, "bold"),
                            bg = highFrameBg, fg = "green",
                            width = 25)

    userLabel.grid(row = 0, column = 1, pady = 5, padx = 20)

    detectCoordsButton = MyButton(highFrame, text = "Detect Coords",
                                bg = "blue", fg = "white",
                                font = (fontStyle, 14), borderwidth = 3
                                )
    detectCoordsButton.grid(row = 0, column = 2, padx = 10)

    newGroupButton = MyButton(highFrame, text = "New Group",
                            bg = "orange", fg = "white",
                            font = (fontStyle, 14), borderwidth = 3
                            )
    newGroupButton.grid(row = 0, column = 3, padx = 10)

    importGroupButton = MyButton(highFrame, text = "Import Group",
                                bg = "green", fg = "white",
                                font = (fontStyle, 14), borderwidth = 3
                                )
    importGroupButton.grid(row = 0, column = 4, padx = 10)

    buyCoffeeButton = MyButton(highFrame, text = "☕ Buy me a coffee",
                                    font = (fontStyle, 14, "bold"),
                                    borderwidth = 3, fg = "black", 
                                    bg = "yellow"
                                    )
    buyCoffeeButton.grid(row = 0, column = 5, padx = (10, 0))

    # TasksFrame
    groupTasksFrame = tkinter.Frame(root)
    groupTasksFrame.pack()

    # Listbox with ScrollBar
    tasksListBox = tkinter.Listbox(
        groupTasksFrame, bg = "orange",
        fg = "black",
        selectbackground = "gray",
        font = (fontStyle, 20, "bold"),
        exportselection = False
    )
    
    tasksListBox.bind('<Double-Button-1>', 
                      lambda event: onClick("DoubleClick Group"))


    scrollbar = tkinter.Scrollbar(
        groupTasksFrame, command = tasksListBox.yview
        )

    tasksListBox.configure(yscrollcommand = scrollbar.set)


    tasksListBox.bind('<<ListboxSelect>>', lambda _: onClick("Select Group"))

    tasksListBox.grid(row = 0, column = 0, sticky = "nsew")
    scrollbar.grid(row = 0, column = 1, sticky = "ns")


    for filename in os.listdir(tasksDir):
        filePath = os.path.join(tasksDir, filename)
        taskGroups.append(TaskGroup(filePath))
        filePaths[taskGroups[-1]] = filePath
        
    for taskGroup in taskGroups:
        tasksListBox.insert(
            "end", taskGroup.title
            )

    chosenGroupFrame = tkinter.Frame(groupTasksFrame, width = 900, height = 740,
                                    bg = "blue"
                                    )
    chosenGroupFrame.grid(row = 0, column = 2)
    chosenGroupFrame.grid_propagate(False)
    
    def displaySelected():
        toolBarFrame = tkinter.Frame(
            chosenGroupFrame,
            bg = "cyan",
            width = 900, height = 50
            )

        toolBarFrame.grid(row = 0, column = 0, sticky = "ew")
        toolBarFrame.grid_propagate(False)
        
        titleLabel = tkinter.Label(
            toolBarFrame,
            text = f"By {selectedGroup.author}",
            bg = "cyan",
            fg = "navy",
            font = (fontStyle, 16, "bold"),
            anchor = "w",
            width = 43
            )
        titleLabel.grid(row = 0, column = 0, 
                        padx = 10, pady = 10, 
                        sticky = "w")
        
        # Add Task Button
        
        addTaskBtn = MyButton(
            toolBarFrame,
            text = "Add Task",
            bg = "blue",
            font = (fontStyle, 16, "bold"),
            width = 8,
            borderwidth = 3
        )
        
        addTaskBtn.grid(row = 0, column = 1, padx = 5, pady = 3)
        
        # Bouton Share
        shareButton = MyButton(
            toolBarFrame,
            text = "Share",
            bg = "green",
            fg = "white",
            font = (fontStyle, 16, "bold"),
            width = 8,
            relief = "raised",
            borderwidth = 3
            )
        shareButton.grid(row = 0, column = 2, padx = 5, pady = 3)
        
        # Bouton Run
        runGroupButton = MyButton(
            toolBarFrame,
            text = "Run Group",
            bg = "red",
            fg = "white",
            font = (fontStyle, 16, "bold"),
            width = 8,
            relief = "raised",
            borderwidth = 3
            )
        runGroupButton.grid(row = 0, column = 3, padx = 5, pady = 3)
        

        # Main frame configuration
        tasksFrame = tkinter.Frame(
            chosenGroupFrame,
            bg="blue",
            width=900, 
            height=690
        )

        tasksFrame.grid(row=1, column=0, sticky="nesw")
        tasksFrame.pack_propagate(False)
        tasksFrame.grid_propagate(False)

        headers = ["Description", "Command", "Arguments", "Times"]
        for i, header in enumerate(headers):
            headerLabel = tkinter.Label(
                tasksFrame,
                text=header,
                bg="darkgray",
                fg="white",
                font=(fontStyle, 12, "bold"),
                relief="raised",
                bd=1
            )
            headerLabel.grid(row=0, column=i, sticky="ew", padx=1, pady=1)

        # Widget creation for each task
        backup = {}
        for row, task in enumerate(selectedGroup.tasks, start = 1):
            # Column 1: Entry for description (default task.desc)
            command, args = str(task).split("  ")[:2]
            args = ",".join(args.split(" "))
            descEntry = tkinter.Entry(
                tasksFrame,
                font=(fontStyle, 16),
                relief="solid",
                bd = 1,
                width = 27
            )
            descEntry.insert(0, task.desc)
            descEntry.grid(row=row, column=0, sticky="ew", padx=2, pady=2)
            
            # Column 2: OptionMenu for commands
            commandVar = tkinter.StringVar(tasksFrame)
            commandVar.set(command)  # Default value
            commandMenu = tkinter.OptionMenu(
                tasksFrame,
                commandVar,
                *matchAction.keys()  # Your global commands list
            )
            commandMenu.config(
                font = (fontStyle, 16,"bold"),
                relief = "solid",
                bd = 1,
                fg = "violet",
                width = 7
            )
            commandMenu.grid(row=row, column=1, sticky="ew", padx=2, pady=2)
            
            # Column 3: Entry for arguments
            argsEntry = tkinter.Entry(
                tasksFrame,
                font = (fontStyle, 16),
                relief = "solid",
                bd = 1,
                justify = "center"
            )
            
            argsEntry.insert(0, args.replace("[SPACE]", " "))
            argsEntry.grid(row=row, column=2, sticky="ew", padx=2, pady=2)
            
            # Column 4: Entry for Times
            timesEntry = tkinter.Entry(
                tasksFrame,
                font=(fontStyle, 16),
                relief = "solid",
                bd = 1, 
                justify = "center",
                width = 6
            )
            timesEntry.insert(0, str(task.times))
            
            timesEntry.grid(row=row, column=3, sticky="ew", padx=2, pady=2)
            
            # Column 5: Validate Button
            runTaskBtn = MyButton(
                tasksFrame,
                text="Run",
                font=(fontStyle, 16, "bold"),
                bg="#4CAF50",
                fg="white",
                relief="raised",
                bd=2,
                cursor="hand2"
            )
            runTaskBtn.grid(
                row = row, column=4, 
                sticky="ew", 
                padx=2, pady=2
                )
            
            # Column 6: Save Button
            saveBtn = MyButton(
                tasksFrame,
                text="Save",
                font=(fontStyle, 16, "bold"),
                bg="#2196F3",
                fg="white",
                relief="raised",
                bd=2,
                cursor="hand2"
            )
            saveBtn.grid(row=row, column=5, sticky="ew", 
                         padx = 2, pady = 2)
            
            
            delButton = MyButton(
                tasksFrame, 
                text = "❌",
                bg = "red",
                borderwidth = 6,
                cursor = "hand2",
            )
            delButton.grid(row = row, column = 6, sticky = "ew", 
                           padx = 2, pady = 2)
            
            
            # Store widgets for future reference
            backup[task] = {
                'run': runTaskBtn,
                'save': saveBtn
            }
            backup[runTaskBtn]= {
                "task": task
            }
            backup[delButton] = {
                "task": task
            }
            
            backup[saveBtn] = {
                "args": argsEntry,
                'command': commandVar,
                'desc': descEntry,
                "times": timesEntry,
                "task": task
            }
            
            
            
            widgets.update(backup)

    


    root.mainloop()
    
main()