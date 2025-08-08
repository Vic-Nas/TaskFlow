
from imports.settings import logged, login, color, getSetting, setSetting
from imports.utils import centerWin
import webbrowser
from pathlib import Path
from imports.automate.TaskDef import TaskGroup, matchAction, Task
from tkinter import filedialog, messagebox
from shutil import copy, copy2
from imports.automate.detectCoords import SimpleCircleOverlay

from pymsgbox import prompt, alert
import tkinter, sys, pyautogui, subprocess, os, socket
from imports.mail import sendFeedBackMail

overlay = None
feedBackWindow = None

def single_instance(port=65432):
    """Prevent multiple instances by binding a local TCP port."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", port))
    except socket.error:
        print("Application is already running.")
        sys.exit(0)
    return s  # Keep socket open as long as app runs

# ---- Usage ----
lock_socket = single_instance()

def updateWindows():
    import tkinter as tk
    import tkinter.ttk as ttk
    import urllib.request
    import json
    
    try:
        # Get local version
        localVersion = getSetting("version")
        
        # Get repository version
        repoUrl = "https://raw.githubusercontent.com/Vic-Nas/TaskFlow/main/data/settings.json"
        
        with urllib.request.urlopen(repoUrl, timeout=10) as response:
            repoSettings = json.loads(response.read().decode('utf-8'))
        
        repoVersion = repoSettings.get("version")
        
        # Ensure repoVersion is an integer
        if repoVersion is None:
            return
        
        try:
            repoVersion = int(repoVersion)
        except (ValueError, TypeError):
            return
        
        # Check if update is needed
        if localVersion == repoVersion:
            alert("Up to date.")
            return
        
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, Exception):
        return
    
    alert("Comfirm update")
    
    tempDir = os.path.abspath("tempUpdate")
    backupDir = os.path.abspath("backup")
    
    # Get the actual executable path (works for both .py and .exe)
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        currentExePath = sys.executable
        appDir = os.path.dirname(currentExePath)
    else:
        # Running as python script
        currentExePath = os.path.abspath(sys.argv[0])
        appDir = os.path.dirname(currentExePath)
    
    exeName = os.path.basename(currentExePath)
    
    # Create temp and backup dirs
    os.makedirs(tempDir, exist_ok=True)
    os.makedirs(backupDir, exist_ok=True)
    
    # Create batch script FIRST, then update version after successful download
    batScript = f"""@echo off
echo Update started - Local version: {localVersion}, Repository version: {repoVersion} > update.log

echo Creating backup... >> update.log
copy "{currentExePath}" "{backupDir}\\{exeName}.bak" >> update.log 2>&1
if errorlevel 1 (
    echo Backup failed, aborting update >> update.log
    goto :cleanup
)

echo Downloading TaskFlow.exe... >> update.log
powershell -WindowStyle Hidden -Command "try {{ Invoke-WebRequest -Uri 'https://github.com/Vic-Nas/TaskFlow/raw/main/build/dist/TaskFlow/TaskFlow.exe' -OutFile '{tempDir}\\TaskFlow.exe' -TimeoutSec 30 }} catch {{ exit 1 }}" >> update.log 2>&1
if errorlevel 1 (
    echo Download failed >> update.log
    goto :cleanup
)

echo Waiting for app to close... >> update.log
timeout /t 3 /nobreak > nul

echo Installing update... >> update.log
copy /y "{tempDir}\\TaskFlow.exe" "{currentExePath}" >> update.log 2>&1
if errorlevel 1 (
    echo Installation failed, restoring backup >> update.log
    copy /y "{backupDir}\\{exeName}.bak" "{currentExePath}" >> update.log 2>&1
    goto :cleanup
)

echo Update successful, starting application... >> update.log
start "" "{currentExePath}"

:cleanup
echo Cleaning up... >> update.log
if exist "{tempDir}" rmdir /s /q "{tempDir}" >> update.log 2>&1
echo Update finished >> update.log
del "%~0"
"""
    
    batPath = os.path.join(os.path.dirname(currentExePath), "update.bat")
    
    with open(batPath, "w") as batFile:
        batFile.write(batScript)
    
    # Update version only AFTER successful batch creation
    # The new version will update its own settings when it starts
    try:
        # Only update if we got this far successfully
        setSetting("version", repoVersion)
    except:
        # If setting fails, don't abort the update
        pass
    
    # Launch batch silently and exit current process
    subprocess.Popen([batPath], cwd=os.path.dirname(currentExePath), creationflags=subprocess.CREATE_NO_WINDOW)
    
    # Exit current process to avoid relaunch loop
    sys.exit(0)
    
    
def reload():
    print(color("Reloading window", "cyan"))
    root.destroy()
    main()

def main():
    global root, overlay, feedBackWindow
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


    def onClick(buttonText, ref1 = None, ref2 = None):
        global selectedGroup
        global overlay, feedBackWindow
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
                alert("Send mouse to a corner to stop everything.")
                times = runGroupTimesEntry.get()
                try:
                    times = int(times)
                    for _ in range(times):
                        for task in selectedGroup.tasks:
                            widgets[task]["run"].invoke()
                except:
                    runGroupTimesEntry.delete(0, "end")
                    runGroupTimesEntry.insert(0, "1")
                    onClick("Run Group")          
                    
            case "New Group":
                title = prompt("Group name: ")
                group = TaskGroup(title = title, 
                                  author = getSetting("email")
                                  )
                group.tasks.append(Task("WAIT  1  1  No description"))
                group.saveAt(Path("tasks")/f"{group.title}.task")
                reload()
                
            case "DoubleClick Group":
                sure = prompt(f"Sure you want to delete {selectedGroup.title} ?(Y or N)")
                if sure and sure[0].lower() == "y":
                    os.remove(filePaths[selectedGroup])
                    reload()
                else:
                    alert("Canceled")
                
            case "Detect Coords":
                if overlay:
                    overlay.close_app()
                overlay = SimpleCircleOverlay()
                overlay.run()
                    
            case "❌":
                task = widgets[ref1]["task"]
                selectedGroup.tasks.remove(task)
                selectedGroup.saveAt(filePaths[selectedGroup])
                onClick("Select Group")
                
            case "➕":
                task = widgets[ref1]["task"]
                newTask = Task("WAIT  1  1  No description")
                try:
                    selectedGroup.insert(selectedGroup.tasks.index(task) + 1, newTask)
                    selectedGroup.saveAt(filePaths[selectedGroup])
                    onClick("Select Group")
                except:
                    message = f"Maximum number of tasks of this group: {selectedGroup.maxTasks}\n"
                    message += "But you can combine task groups with EXEC command"
                    alert(message)
                    
                    
            case "Run":
                try:
                    widgets[widgets[ref1]["task"]]["save"].invoke()
                    widgets[ref1]["task"].run()
                    
                except pyautogui.FailSafeException:
                    print("Failsafe activated - TaskFlow will exit")
                    alert("Failsafe triggered! TaskFlow is shutting down.")
                    os._exit(0)
                    
                except Exception as e:
                    print(e)
                    alert(f"Can't run that task:\n{e}")
                
            case "Save":
                try:
                    params = " ".join(widgets[ref1]["args"].get().replace(" ", "[SPACE]").split(","))
                    command = widgets[ref1]["command"].get()
                    desc = widgets[ref1]["desc"].get()
                    times = widgets[ref1]["times"].get()
                    newTask = Task("  ".join(
                        [command, params, times, desc]
                    ))
                    widgets[ref1]["task"].update(newTask)
                    selectedGroup.saveAt(filePaths[selectedGroup])
            
                except Exception as e:
                    alert("Error in Task")
                    print(e)
                    
            case "LCLICK" | "RCLICK":
                onClick("Detect Coords")
                
            case "EXEC":
                # Clear the entry
                widgets[ref1]["entry"].delete(0, tkinter.END)
                
                # Open file dialog to select a file
                file_selected = filedialog.askopenfilename(
                    title="Select a file to open",
                    initialdir=os.getcwd(),  # or another default directory
                    filetypes=[
                        ("Task file", "*.task")
                    ]
                )
                
                # If a file was selected
                if file_selected:
                    # Normalize the path and insert it into the entry
                    normalized_path = os.path.normpath(file_selected)
                    widgets[ref1]["entry"].insert(0, normalized_path)
                else:
                    # If no file selected, reset commandMenu to "WAIT"
                    ref2.set("WAIT")
                    ref1.configure(text = "WAIT")
            
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
                    
            case "TaskFlow":
                webbrowser.open("https://vic-nas.github.io/TaskFlow/")
                print("Visiting website")
                
            case "OPEN":
                # Clear the entry
                widgets[ref1]["entry"].delete(0, tkinter.END)
                
                # Open file dialog to select a file
                file_selected = filedialog.askopenfilename(
                    title="Select a file to open",
                    initialdir=os.getcwd(),  # or another default directory
                    filetypes=[
                        ("All files", "*.*"),
                        ("Text files", "*.txt"),
                        ("Python files", "*.py"),
                        # Add other file types as needed
                    ]
                )
                
                # If a file was selected
                if file_selected:
                    # Normalize the path and insert it into the entry
                    normalized_path = os.path.normpath(file_selected)
                    widgets[ref1]["entry"].insert(0, normalized_path)
                else:
                    # If no file selected, reset commandMenu to "WAIT"
                    ref2.set("WAIT")
                    ref1.configure(text = "WAIT")
            
            case "FeedBack":
                if feedBackWindow:
                    feedBackWindow.destroy()

                feedBackWindow = tkinter.Toplevel()
                feedBackWindow.title("Send Feedback")
                feedBackWindow.geometry("400x350")
                centerWin(feedBackWindow)
                feedBackWindow.transient()  # Reste devant la fenêtre principale
                feedBackWindow.grab_set()   # Bloque l’interaction avec les autres fenêtres tant que celle-ci est ouverte

                attachedFiles = []

                def selectFiles():
                    files = filedialog.askopenfilenames(title="Select files")
                    if files:
                        # Ajouter seulement les fichiers non encore présents
                        newFiles = [f for f in files if f not in attachedFiles]
                        attachedFiles.extend(newFiles)

                        # Mettre à jour l’affichage des noms
                        fileListVar.set("\n".join([f.split("/")[-1] for f in attachedFiles]))

                def send():
                    text = textBox.get("1.0", "end").strip()
                    if not text:
                        messagebox.showwarning("Empty", "Please write some feedback.")
                        return
                    try:
                        sendFeedBackMail(getSetting("email"), text, *attachedFiles)
                        messagebox.showinfo("Sent", "Feedback sent successfully.")
                        feedBackWindow.destroy()
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to send feedback:\n{e}")

                textBox = tkinter.Text(feedBackWindow, height=8, wrap="word")
                textBox.pack(padx=10, pady=(10, 5), fill="x")

                selectBtn = tkinter.Button(feedBackWindow, text="Add files", command=selectFiles)
                selectBtn.pack(padx=10, pady=(5, 2))

                fileListVar = tkinter.StringVar(value="No files selected")
                fileLabel = tkinter.Label(feedBackWindow, textvariable=fileListVar, anchor="w", justify="left")
                fileLabel.pack(padx=10, pady=(0, 5), fill="x")

                sendBtn = tkinter.Button(feedBackWindow, text="Send", command=send)
                sendBtn.pack(padx=10, pady=10)


            case default:  # default case
                print(color(buttonText, "red"), "clicked.")
                if default not in matchAction.keys():
                    alert("Unavailable for now.")

    class MyButton(tkinter.Button):
        def __init__(self, master, **kwargs):
            # Si aucune command n'est fournie, utiliser onClick par défaut
            if 'command' not in kwargs:
                kwargs['command'] = lambda: onClick(self['text'], ref1=self)
            
            super().__init__(master, **kwargs)
            
    # High Frame
    highFrameBg = "violet"
    highFrame = tkinter.Frame(root, bg = highFrameBg, width = 1200, 
                            height = 60
                            )
    highFrame.pack()
    highFrame.grid_propagate(False)

    taskFlowButton = MyButton(
        highFrame, 
        text = "TaskFlow v" + str(getSetting("version")), 
        borderwidth = 0, font = (fontStyle, 20, "bold"), 
        bg = highFrameBg, fg = "white",
    )

    taskFlowButton.grid(row = 0, column = 0, pady = 5)

    userLabel = tkinter.Label(highFrame, text = getSetting("email"), 
                            font = (fontStyle, 20, "bold"),
                            bg = highFrameBg, fg = "green",
                            width = 25)

    userLabel.grid(row = 0, column = 1, pady = 5, padx = 20)

    feedBackButton = MyButton(highFrame, text = "FeedBack",
                                bg = "blue", fg = "white",
                                font = (fontStyle, 14), borderwidth = 3
                                )
    feedBackButton.grid(row = 0, column = 2, padx = 10)

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
        global runGroupTimesEntry
        toolBarFrameBg = "cyan"
        toolBarFrame = tkinter.Frame(
            chosenGroupFrame,
            bg = toolBarFrameBg,
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
        
        # Share
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
        shareButton.grid(row = 0, column = 1, padx = 5, pady = 3)
        
        # Run
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
        runGroupButton.grid(row = 0, column = 2, padx = 3, pady = 3)
        
        # Times Entry
        runGroupTimesEntry = tkinter.Entry(
            toolBarFrame,
            width = 2,
            font = (fontStyle, 22, "bold"),
            bg = "white",
            fg = "blue",
        )
        runGroupTimesEntry.insert(0, "1")
        runGroupTimesEntry.grid(row = 0, column = 3, padx = 3, pady = 3)
        
        timesLabel = tkinter.Label(
            toolBarFrame,
            width = 5,
            font = (fontStyle, 20, "bold"),
            bg = toolBarFrameBg,
            text = "time(s)"
        )
        timesLabel.grid(row = 0, column = 4, padx = 2, pady = 3)
        

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
                width = 26
            )
            descEntry.insert(0, task.desc)
            descEntry.grid(row=row, column=0, sticky="ew", padx=2, pady=2)
            
            # Column 2: OptionMenu for commands
            commandVar = tkinter.StringVar(tasksFrame)
            commandVar.set(command)  # Default value
            commandMenu = tkinter.OptionMenu(
                tasksFrame,
                commandVar,
                *matchAction.keys()
            )
            commandMenu.config(
                font=(fontStyle, 16, "bold"),
                relief="solid",
                bd=1,
                fg="violet", 
                width=7
            )

            commandVar.trace('w', lambda *args: onClick(commandVar.get(), commandMenu, commandVar))
            commandMenu.grid(row=row, column=1, sticky="ew", padx=2, pady=2)
            
            # Column 3: Entry for arguments
            argsEntry = tkinter.Entry(
                tasksFrame,
                font = (fontStyle, 16),
                relief = "solid",
                bd = 1,
                justify = "center",
                width = 18
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
                borderwidth = 5,
                cursor = "hand2",
            )
            delButton.grid(row = row, column = 6, sticky = "ew", 
                           padx = 2, pady = 2)
            
            addDownButton = MyButton(
                tasksFrame, 
                text = "➕",
                bg = "gray",
                borderwidth = 5,
                cursor = "hand2",
            )
            addDownButton.grid(row = row, column = 7, sticky = "ew", 
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
            backup[addDownButton] = {
                "task": task
            }
            
            
            backup[commandMenu] = {
                "entry": argsEntry
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