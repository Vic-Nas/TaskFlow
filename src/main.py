
from imports.settings import logged, login, color, getSetting
from imports.utils import centerWin, submitFormAsync
import webbrowser, traceback
from pathlib import Path
from imports.automate.TaskDef import TaskGroup, matchAction, Task
from tkinter import filedialog, messagebox
from shutil import copy, copy2
from imports.automate.detectCoords import SimpleCircleOverlay

from pymsgbox import prompt
from imports.utils import alert
import tkinter, sys, pyautogui, os, socket
from imports.mail import sendFeedBackMail
import threading

overlay = None
feedBackWindow = None
MAX_ITEMS = 14
displayStartIndex = 0


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


def loadGroups():
    # Clear existing data first
    global taskGroups, filePaths
    taskGroups.clear()
    filePaths.clear()
    tasksListBox.delete(0, "end")
    
    if not os.path.exists(tasksDir):
        return
        
    for filename in os.listdir(tasksDir):
        if not filename.endswith('.task'):  # Validate file type
            continue
        filePath = os.path.join(tasksDir, filename)
        try:
            taskGroups.append(TaskGroup(filePath))
            filePaths[taskGroups[-1]] = filePath
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            continue
            
    goodGroup = lambda group: group.title.lower().startswith(searchEntryVar.get().lower())
    for taskGroup in filter(goodGroup, taskGroups):
        tasksListBox.insert("end", taskGroup.title)

selectedGroup = None
filePaths = {}
tasksDir = "tasks"
taskGroups: list[TaskGroup] = []

if not logged():
    login()
    
if not logged():
    alert("You must log in")
    sys.exit()
    
root = tkinter.Tk()
root.geometry("1200x800")
# root.resizable(True, True)
root.iconbitmap(Path("data")/"VN.ico")
root.title("TaskFlow")


centerWin(root)
fontStyle = "Times New Roman"
root.deiconify()
root.lift()
root.focus_force()



def onClick(buttonText, task=None):
    global selectedGroup, displayStartIndex, overlay, feedBackWindow, X, Y
    
    try:
        match buttonText:
            case "☕ Buy me a coffee":
                webbrowser.open("https://coff.ee/vicnas")
                print("Buying coffee")
                
            case "Select Group":
                # FIX: Check if selection exists and handle filtering
                selection = tasksListBox.curselection()
                if not selection:
                    return
                
                # Get filtered list for correct index mapping
                goodGroup = lambda group: group.title.startswith(searchEntryVar.get())
                filteredGroups = list(filter(goodGroup, taskGroups))
                
                if selection[0] >= len(filteredGroups):
                    return
                    
                for widget in chosenGroupFrame.winfo_children():
                    widget.destroy()
                    
                selectedGroup = filteredGroups[selection[0]]
                size = len(selectedGroup.tasks)
                start = displayStartIndex
                
                if size <= MAX_ITEMS:
                    start = 0
                elif start > size - MAX_ITEMS:
                    # FIX: Prevent negative start
                    start = max(0, size - MAX_ITEMS)
                    
                displayStartIndex = start
                displaySelected(
                    leftUp=start, 
                    leftDown=max(0, size - start - MAX_ITEMS)
                )

            case "Import Group":
                filePath = filedialog.askopenfilename(
                    title="Choose .task file",
                    filetypes=[("Task file", "*.task")]
                )
                print(color("Chose to open file:", "blue"), 
                    filePath if filePath else None)
                
                if filePath:
                    # FIX: Validate file exists
                    if os.path.exists(filePath):
                        try:
                            copy(filePath, Path("tasks"))
                            loadGroups()
                        except Exception as e:
                            alert(f"Error importing file: {e}")
                    else:
                        alert("File does not exist")

            case "Run Group":
                if not selectedGroup:
                    alert("No group selected")
                    return
                    
                alert("Send mouse to a corner to stop everything.")
                times_str = runGroupTimesEntry.get()
                root.withdraw()
                try:
                    # FIX: Validate integer input
                    times = int(times_str)
                    if times <= 0:
                        raise ValueError("Times must be positive")
                        
                    for _ in range(times):
                        for task in selectedGroup.tasks:
                            task.run()
                            
                except pyautogui.FailSafeException:
                    print("Failsafe activated - TaskFlow will exit")
                    alert("Failsafe triggered! TaskFlow is shutting down.")
                    os._exit(0)
                except ValueError:
                    runGroupTimesEntry.delete(0, "end")
                    runGroupTimesEntry.insert(0, "1")
                    alert("Please enter a valid positive number")
                except Exception as e:
                    alert(f"Problem running this group: {e}")
                finally:
                    root.deiconify()

            case "New Group":
                title = prompt("Group name: ")
                if title:
                    try:
                        group = TaskGroup(title=title, author=getSetting("email"))
                        group.tasks.append(Task("WAIT  1  1  No description"))
                        group.saveAt(Path("tasks")/f"{group.title}.task")
                        loadGroups()
                    except Exception as e:
                        alert(f"Error creating group: {e}")

            case "🗙":
                if selectedGroup:
                    if messagebox.askyesno("Confirmation", f"Sure you want to delete {selectedGroup.title}?"):
                        try:
                            os.remove(filePaths[selectedGroup])
                            selectedGroup = None  # Clear selection
                            loadGroups()
                        except Exception as e:
                            alert(f"Error deleting group: {e}")

            case "DoubleClick Group":
                if not selectedGroup:
                    return
                title = prompt(f"Rename {selectedGroup.title} to:")
                if title:
                    try:
                        selectedGroup.title = title
                        selectedGroup.saveAt(filePaths[selectedGroup])
                        loadGroups()
                    except Exception as e:
                        alert(f"Error renaming group: {e}")

            case "Detect Coords":
                try:
                    if overlay:
                        overlay.closeApp()
                    overlay = SimpleCircleOverlay(screenshotPath="screenshot.jpg", screenshotPathCircle="screenshotC.jpg", wantClickInfo=100)
                    root.withdraw()
                    X, Y, moved, desc = overlay.run()
                    root.deiconify()
                    if task["descEntryVar"].get().startswith("No description"):
                        texts = desc.split("+")
                        for i in range(len(texts)):
                            texts[i] = texts[i].split(",")[0]
                        text = ".".join(texts)
                        task["descEntryVar"].set(text)
                    task["argsEntryVar"].set(f"{X},{Y}")
                except Exception as e:
                    alert(f"Error opening coordinate detector: {e}")
                    
                if moved and getSetting("niceUser"):
                    submitFormAsync(desc, X, Y, ("screenshot.jpg", "screenshotC.jpg"))
                    

            case "❌":
                if task and selectedGroup:
                    try:
                        selectedGroup.tasks.remove(task)
                        selectedGroup.saveAt(filePaths[selectedGroup])
                        onClick("Select Group")
                    except ValueError:
                        pass  # Task already removed
                    except Exception as e:
                        alert(f"Error removing task: {e}")

            case "➕":
                if task and selectedGroup:
                    try:
                        newTask = Task("WAIT  1  1  No description")
                        task_index = selectedGroup.tasks.index(task) + 1
                        selectedGroup.tasks.insert(task_index, newTask)
                        selectedGroup.saveAt(filePaths[selectedGroup])
                        onClick("Select Group")
                    except Exception as e:
                        message = (
                            f"Maximum number of tasks of this group: {selectedGroup.maxTasks}\n"
                            "But you can combine task groups with EXEC command"
                        )
                        alert(message)

            case "Run":
                if not task:
                    return
                try:
                    # FIX: Safe access to task dictionary
                    if "save" in task:
                        task["save"].invoke()
                    root.withdraw()
                    task.run()
                    root.deiconify()
                except pyautogui.FailSafeException:
                    print("Failsafe activated - TaskFlow will exit")
                    alert("Failsafe triggered! TaskFlow is shutting down.")
                    os._exit(0)
                except Exception as e:
                    traceback.print_exc()
                    alert(f"Can't run that task:\n{e}")
                finally:
                    root.deiconify()

            case "Save":
                if not task:
                    return
                try:
                    # FIX: Safe access to task variables
                    if not all(key in task for key in ["argsEntryVar", "commandMenuVar", "descEntryVar", "timesEntryVar"]):
                        alert("Task not properly initialized")
                        return
                        
                    params = " ".join(
                        task["argsEntryVar"].get().replace(" ", "[SPACE]").split(",")
                    )
                    command = task["commandMenuVar"].get()
                    desc = task["descEntryVar"].get()
                    times_str = task["timesEntryVar"].get()
                    
                    # FIX: Validate times input
                    try:
                        times = int(times_str) if times_str.strip() else 1
                        if times <= 0:
                            times = 1
                    except ValueError:
                        times = 1

                    newTask = Task("  ".join([command, params, str(times), desc]))
                    task.update(newTask, False)
                    selectedGroup.saveAt(filePaths[selectedGroup])
                    
                    # Safe button color update
                    if "save" in task:
                        task["save"].config(bg="#2196F3")

                except Exception as e:
                    alert(f"Error saving task: {e}")
                    traceback.print_exc()

            
            case "LCLICK" | "RCLICK":
                root.iconify()
                onClick("Detect Coords", task)


            case "EXEC":
                if task:
                    try:
                        task["argsEntryVar"].set("")
                        fileSelected = filedialog.askopenfilename(
                            title="Select a file to open",
                            initialdir=os.getcwd(),
                            filetypes=[("Task file", "*.task")]
                        )
                        if fileSelected and os.path.exists(fileSelected):
                            normalizedPath = os.path.normpath(fileSelected)
                            task["argsEntryVar"].set(normalizedPath)
                        else:
                            task["commandMenuVar"].set("WAIT")
                            if "commandMenu" in task:
                                task["commandMenu"].configure(text="WAIT")
                    except Exception as e:
                        alert(f"Error selecting EXEC file: {e}")

            case "KEY":
                if task:
                    try:
                        task["argsEntryVar"].set("win,d")
                    except Exception as e:
                        alert(f"Error setting KEY args: {e}")

            case "Share":
                if not selectedGroup:
                    alert("No group selected to share")
                    return
                    
                folderPath = filedialog.askdirectory(
                    title="Select folder to save task file",
                    initialdir="."
                )
                if folderPath:
                    try:
                        destination = os.path.join(
                            folderPath,
                            f"{selectedGroup.title.replace(' ', '_')}.task"
                        )
                        copy2(filePaths[selectedGroup], destination)
                        alert(f"Task file saved to: {destination}")
                    except Exception as e:
                        alert(f"Error sharing file: {e}")
                        traceback.print_exc()

            case t if t.startswith("TaskFlow"):
                webbrowser.open("https://vic-nas.github.io/TaskFlow/")
                print("Visiting website")

            case "OPEN":
                if task:
                    try:
                        task["argsEntryVar"].set("")
                        fileSelected = filedialog.askopenfilename(
                            title="Select a file to open",
                            initialdir=os.getcwd(),
                            filetypes=[
                                ("All files", "*.*"),
                                ("Text files", "*.txt"),
                                ("Python files", "*.py"),
                            ]
                        )
                        if fileSelected and os.path.exists(fileSelected):
                            normalizedPath = os.path.normpath(fileSelected)
                            task["argsEntryVar"].set(normalizedPath)
                        else:
                            task["commandMenuVar"].set("WAIT")
                            if "commandMenu" in task:
                                task["commandMenu"].configure(text="WAIT")
                    except Exception as e:
                        alert(f"Error selecting OPEN file: {e}")

            case "modify":
                if task and "save" in task:
                    try:
                        task["save"].config(bg="red")
                    except Exception as e:
                        print(f"Error updating save button color: {e}")

            case b if b.startswith("⬆"):
                displayStartIndex = max(0, displayStartIndex - 1)
                onClick("Select Group")

            case b if b.startswith("⬇"):
                if selectedGroup:
                    max_start = len(selectedGroup.tasks) - MAX_ITEMS
                    if displayStartIndex < max_start:
                        displayStartIndex += 1
                        onClick("Select Group")

            case "FeedBack":
                try:
                    if feedBackWindow:
                        feedBackWindow.destroy()
                        feedBackWindow = None
                        
                    feedBackWindow = tkinter.Toplevel()
                    feedBackWindow.title("Send Feedback")
                    feedBackWindow.geometry("420x380")
                    centerWin(feedBackWindow)
                    feedBackWindow.transient()
                    feedBackWindow.grab_set()
                    feedBackWindow.configure(bg="#1e1e2f")
                    attachedFiles = []
                    
                    def selectFiles(files=None):
                        try:
                            if not files:
                                files = filedialog.askopenfilenames(title="Select files")
                            if files:
                                newFiles = [f for f in files if f not in attachedFiles]
                                attachedFiles.extend(newFiles)
                                updateFileList()
                        except Exception as e:
                            alert(f"Error selecting files: {e}")
                    
                    def updateFileList():
                        try:
                            fileListBox.delete(0, "end")
                            if not attachedFiles:
                                fileListBox.insert("end", "No files selected")
                            else:
                                for f in attachedFiles:
                                    fileListBox.insert("end", f.split("/")[-1])
                        except Exception as e:
                            print(f"Error updating file list: {e}")
                    
                    def onDoubleClick(event):
                        try:
                            selection = fileListBox.curselection()
                            if selection and attachedFiles:  
                                index = selection[0]
                                if index < len(attachedFiles):  
                                    removedFile = attachedFiles.pop(index)
                                    print(f"Removed file: {removedFile}")
                                    updateFileList()
                        except Exception as e:
                            print(f"Error removing file: {e}")
                    
                    def send():
                        try:
                            text = textBox.get("1.0", "end").strip()
                            if not text:
                                messagebox.showwarning("Empty", "Please write some feedback.")
                                return
                            sendFeedBackMail(getSetting("email"), text, *attachedFiles)
                            messagebox.showinfo("Sent", "Feedback sent successfully.")
                            feedBackWindow.destroy()
                        except Exception as e:
                            messagebox.showerror("Error", f"Failed to send feedback:\n{e}")
                            traceback.print_exc()
                    
                    # Header
                    header = tkinter.Label(feedBackWindow, text="📢 Send us your feedback",
                                        bg="#2d2d44", fg="white", font=("Segoe UI", 14, "bold"),
                                        pady=10)
                    header.pack(fill="x")
                    
                    # Main content frame
                    content_frame = tkinter.Frame(feedBackWindow, bg="#1e1e2f")
                    content_frame.pack(fill="x", padx=15, pady=(10, 0))
                    
                    # Feedback text
                    textBox = tkinter.Text(content_frame, height=5, wrap="word",
                                        bg="#f0f0f0", fg="#000000",
                                        relief="flat", highlightthickness=1, highlightbackground="#4cc9f0")
                    textBox.pack(fill="x", pady=(0, 8))
                    
                    # Add files button
                    selectBtn = tkinter.Button(content_frame, text="📎 Add files", command=selectFiles,
                                            bg="#4cc9f0", fg="white", activebackground="#3bb0d8",
                                            relief="flat", font=("Segoe UI", 10, "bold"))
                    selectBtn.pack(fill="x", pady=(0, 5))
                    
                    # Helper text
                    helpText = tkinter.Label(content_frame, text="Double-click a file to remove it",
                                            bg="#1e1e2f", fg="#888888", font=("Segoe UI", 9))
                    helpText.pack(anchor="w", pady=(0, 3))
                    
                    # Scrollable file list with fixed height
                    fileFrame = tkinter.Frame(content_frame, bg="#1e1e2f", height=120)
                    fileFrame.pack(fill="x", pady=(0, 8))
                    fileFrame.pack_propagate(False)
                    
                    fileScroll = tkinter.Scrollbar(
                        fileFrame,
                        orient="vertical",
                        bg="lightblue",      
                        troughcolor="white", 
                        activebackground="blue",# Hover
                        relief="flat",         
                        highlightthickness=0
                    )

                    
                    fileListBox = tkinter.Listbox(fileFrame, yscrollcommand=fileScroll.set,
                                                bg="white", fg="black", relief="flat",
                                                selectbackground="#4cc9f0", activestyle="none")
                    fileListBox.pack(side="left", fill="both", expand=True)
                    fileScroll.config(command=fileListBox.yview)
                    
                    # Bind double-click event to the listbox
                    fileListBox.bind("<Double-Button-1>", onDoubleClick)
                    
                    # Fixed bottom button frame
                    bottom_frame = tkinter.Frame(feedBackWindow, bg="#1e1e2f")
                    bottom_frame.pack(fill="x", pady=10)
                    
                    sendBtn = tkinter.Button(bottom_frame, text="📤 Send Feedback", command=send,
                                            bg="#72efdd", fg="#000", activebackground="#56d8c9",
                                            relief="flat", font=("Segoe UI", 11, "bold"))
                    sendBtn.pack(fill="x", padx=15)
                    
                    updateFileList()
                    selectFiles(("logs.txt",))
                    centerWin(feedBackWindow)
                    
                except Exception as e:
                    alert(f"Error opening feedback window: {e}")
                    traceback.print_exc()

            case default:
                print(color(buttonText, "red"), "clicked.")
                if buttonText not in matchAction.keys():
                    alert("Unavailable for now.")

    except Exception as e:
        print(f"Error in onClick '{buttonText}': {e}")
        traceback.print_exc()
        alert(f"An error occurred: {e}")

class MyButton(tkinter.Button):
    def __init__(self, master, **kwargs):
        if 'command' not in kwargs:
            kwargs['command'] = lambda: onClick(self['text'])
        
        super().__init__(master, **kwargs)
        
# High Frame
highFrameBg = "violet"
highFrame = tkinter.Frame(root, bg = highFrameBg, width = 1200, 
                        height = 60
                        )
highFrame.pack()
highFrame.grid_propagate(False)

version = str(getSetting("version"))[:3]  # prend max 3 caractères

taskFlowButton = MyButton(
    highFrame, 
    text = "TaskFlow v" + version, 
    borderwidth = 0, font = (fontStyle, 22, "bold"), 
    bg = highFrameBg, fg = "white", width = 12,
    anchor = "w", justify = "center"
)

taskFlowButton.grid(row = 0, column = 0, pady = 5, padx = (15, 0))


def normalizeEmail(email, maxLen = 35):
    if len(email) == maxLen:
        return email
    if len(email) < maxLen:
        totalSpaces = maxLen - len(email)
        leftSpaces = totalSpaces // 2
        rightSpaces = totalSpaces - leftSpaces
        return " " * leftSpaces + email + " " * rightSpaces

    keepLen = maxLen - 3
    leftLen = keepLen // 2
    rightLen = keepLen - leftLen
    return email[:leftLen] + "..." + email[-rightLen:]




email = getSetting("email")
normalizedEmail = normalizeEmail(email)

userLabel = tkinter.Label(
    highFrame, 
    text=normalizedEmail,
    font = ('Courier', 13, 'bold'),
    bg=highFrameBg, fg="green",
    anchor="w"
)

userLabel.grid(row=0, column=1, pady=5, padx=(8, 20))


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
groupTasksFrame = tkinter.Frame(
    root,
    bg = "red"
    )
groupTasksFrame.pack()


# searchEntry = tkinter.Entry(
#     groupTasksFrame,
#     font = (fontStyle, 16, "bold"),
#     width = 15
    
# )

# searchEntry.grid(
#     row = 0, column = 0,
# )

taskListFrame = tkinter.Frame(
    groupTasksFrame,
)
taskListFrame.grid(row = 0, column = 0)

searchEntryVar = tkinter.StringVar()

searchEntry = tkinter.Entry(
    taskListFrame,
    font=(fontStyle, 16, "bold"),
    fg="#333333",
    bg="#ffffff",
    insertbackground="#555555",
    relief="flat",                    
    highlightthickness=2,           
    highlightbackground="#cccccc",    
    highlightcolor="#0078d7"       ,
    textvariable = searchEntryVar  
)

searchEntry.grid(
    row = 0, column = 0,
)

deleteGroupButton = MyButton(
    taskListFrame,
    text = "🗙",
    justify = "center",
    bg = "red",
    width = 4
)
deleteGroupButton.grid(
    row = 0, column = 1,
    padx = 2
)


# Listbox with ScrollBar
tasksListBox = tkinter.Listbox(
    taskListFrame, bg = "orange",
    fg = "black",
    selectbackground = "gray",
    font = (fontStyle, 20, "bold"),
    exportselection = False,
    height=22,
    width=18
)

tasksListBox.bind('<Double-Button-1>', 
                    lambda event: onClick("DoubleClick Group"))


scrollbar = tkinter.Scrollbar(
    taskListFrame, command = tasksListBox.yview
    )

tasksListBox.configure(yscrollcommand = scrollbar.set)


tasksListBox.bind('<<ListboxSelect>>', lambda _: onClick("Select Group"))

tasksListBox.grid(row = 1, column = 0, sticky = "nsew")
scrollbar.grid(row = 1, column = 1, sticky = "ns")


loadGroups()

chosenGroupFrame = tkinter.Frame(groupTasksFrame, width = 900, height = 740,
                                bg = "blue"
                                )
chosenGroupFrame.grid(row = 0, column = 1)
chosenGroupFrame.grid_propagate(False)

def displaySelected(leftUp = 0, leftDown = 0):
    global runGroupTimesEntry, displayStartIndex
    toolBarFrameBg = "cyan"
    toolBarFrame = tkinter.Frame(
        chosenGroupFrame,
        bg = toolBarFrameBg,
        width = 900, height = 55
        )

    toolBarFrame.grid(row = 0, column = 0, sticky = "ew")
    toolBarFrame.grid_propagate(False)
    
    authorLabel = tkinter.Label(
        toolBarFrame,
        text = f"By {normalizeEmail(selectedGroup.author)}",
        bg = "cyan",
        fg = "navy",
        font = ('Courier', 13, 'bold'),
        anchor = "w",
        )
    authorLabel.grid(row = 0, column = 0, 
                    padx = 10, pady = 2, 
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
    shareButton.grid(row = 0, column = 1, padx = 5, pady = 5)
    
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
    runGroupButton.grid(row = 0, column = 2, padx = 5, pady = 1)
    
    # Times Entry
    runGroupTimesEntry = tkinter.Entry(
        toolBarFrame,
        width = 2,
        font = (fontStyle, 22, "bold"),
        bg = "white",
        fg = "blue",
    )
    runGroupTimesEntry.insert(0, "1")
    runGroupTimesEntry.grid(row = 0, column = 3, padx = 3, pady = 1)
    
    timesLabel = tkinter.Label(
        toolBarFrame,
        width = 5,
        font = (fontStyle, 20, "bold"),
        bg = toolBarFrameBg,
        text = "time(s)"
    )
    timesLabel.grid(row = 0, column = 4, padx = (2, 5), pady = 1)
    
    upButton = MyButton(
        toolBarFrame,
        text = f"⬆{leftUp}",
        bg = "yellow",
        font = (fontStyle, 17, "bold"),
    )
    upButton.grid(row = 0, column = 5, padx = 2, pady = 4)
    
    downButton = MyButton(
        toolBarFrame,
        text = f"⬇{leftDown}",
        bg = "yellow",
        font = (fontStyle, 17, "bold"),
    )
    downButton.grid(row = 0, column = 6, padx = 2, pady = 4)

    # Main frame configuration
    tasksFrame = tkinter.Frame(
        chosenGroupFrame,
        bg="blue",
        width=900, 
        height=690
    )

    tasksFrame.grid(row=1, column=0, sticky="nesw")
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

    
    
    for row, task in enumerate(selectedGroup.tasks[displayStartIndex:], start = 1):
        # Column 1: Entry for description (default task.desc)
        
        command, args = str(task).split("  ")[:2]
        args = ",".join(args.split(" "))
        descEntryVar = tkinter.StringVar()
        descEntry = tkinter.Entry(
            tasksFrame,
            font=(fontStyle, 16),
            relief="solid",
            bd = 1,
            width = 26, 
            textvariable = descEntryVar,
        )
        descEntryVar.set(task.desc)
        
        descEntry.grid(row=row, column=0, sticky="ew", padx=2, pady=2)
        
        # Column 2: OptionMenu for commands
        commandMenuVar = tkinter.StringVar(tasksFrame)
        commandMenuVar.set(command)  # Default value
        commandMenu = tkinter.OptionMenu(
            tasksFrame,
            commandMenuVar,
            *matchAction.keys(),
            command = lambda varVal, t=task: onClick(varVal, t),
        )
        commandMenu.config(
            font=(fontStyle, 16, "bold"),
            relief="solid",
            bd=1,
            fg="violet", 
            width=7
        )

        # commandMenuVar.trace('w', lambda *args: onClick(commandMenuVar.get(), commandMenu, commandMenuVar))
        commandMenu.grid(row=row, column=1, sticky="ew", padx=2, pady=2)
        
        
        # Column 3: Entry for arguments
        argsEntryVar = tkinter.StringVar()
        
        argsEntry = tkinter.Entry(
            tasksFrame,
            font = (fontStyle, 16),
            relief = "solid",
            bd = 1,
            justify = "center",
            width = 18, 
            textvariable = argsEntryVar
        )
        
        argsEntryVar.set(args.replace("[SPACE]", " "))
        argsEntry.grid(row=row, column=2, sticky="ew", padx=2, pady=2)
        
        # Column 4: Entry for Times
        timesEntryVar = tkinter.StringVar()
        
        timesEntry = tkinter.Entry(
            tasksFrame,
            font=(fontStyle, 16),
            relief = "solid",
            bd = 1, 
            justify = "center",
            width = 6,
            textvariable = timesEntryVar
        )
        timesEntryVar.set(str(task.times))
        
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
            cursor="hand2",
            command = lambda t=task: onClick("Run", t)
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
            cursor="hand2",
            command = lambda t=task: onClick("Save", t)
            
        )
        saveBtn.grid(row=row, column=5, sticky="ew", 
                        padx = 2, pady = 2)
        
        
        delButton = MyButton(
            tasksFrame, 
            text = "❌",
            bg = "red",
            borderwidth = 5,
            cursor = "hand2",
            command = lambda t=task: onClick("❌", t)
        )
        delButton.grid(row = row, column = 6, sticky = "ew", 
                        padx = 2, pady = 2)
        
        addDownButton = MyButton(
            tasksFrame, 
            text = "➕",
            bg = "gray",
            borderwidth = 5,
            cursor = "hand2",
            command = lambda t=task: onClick("➕", t)
        )
        addDownButton.grid(row = row, column = 7, sticky = "ew", 
                        padx = 2, pady = 2)

        
        task.update(
            {
                "run": runTaskBtn,
                "save": saveBtn,
                "del": delButton,
                "addDown": addDownButton,
                "commandMenu": commandMenu,
                "commandMenuVar": commandMenuVar,
                "argsEntryVar": argsEntryVar,
                "descEntryVar": descEntryVar,
                "timesEntryVar": timesEntryVar
            }
        )

        
        commandMenuVar.trace_add("write", lambda *_, t=task: onClick("modify", t))
        descEntryVar.trace_add("write", lambda *_, t=task: onClick("modify", t))
        argsEntryVar.trace_add("write", lambda *_, t=task: onClick("modify", t))
        timesEntryVar.trace_add("write", lambda *_, t=task: onClick("modify", t))
        



# FIX 3: Better search handling
def on_search_change(*args):
    try:
        loadGroups()
    except Exception as e:
        print(f"Search error: {e}")

searchEntryVar.trace_add("write", on_search_change)

root.mainloop()
