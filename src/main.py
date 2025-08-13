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


overlay = None
feedBackWindow = None
MAX_ITEMS = 18  # Increased default further
displayStartIndex = 0


def singleInstance(port=65432):
    """Prevent multiple instances by binding a local TCP port."""
    import socket
    import sys
    import tkinter as tk
    from tkinter import messagebox
    import psutil
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", port))
    except socket.error:
        # Application is already running, show dialog
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        result = messagebox.askyesno(
            "Application Already Running",
            "Another instance of this application is already running.\n\nDo you want to close the existing instance and start a new one?",
            icon="question"
        )
        
        root.destroy()
        
        if result:  # User clicked Yes
            try:
                # Find and terminate the process using the port
                for conn in psutil.net_connections():
                    if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                        try:
                            process = psutil.Process(conn.pid)
                            process.terminate()  # Graceful termination
                            process.wait(timeout=5)  # Wait up to 5 seconds
                            break
                        except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                            # If graceful termination fails, force kill
                            try:
                                process.kill()
                            except psutil.NoSuchProcess:
                                pass
                            break
                
                # Try to bind again after closing the old instance
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.bind(("127.0.0.1", port))
                print("Existing instance closed. Starting new instance...")
            except Exception as e:
                print(f"Error closing existing instance: {e}")
                sys.exit(1)
        else:  # User clicked No
            print("Keeping existing instance. Exiting...")
            sys.exit(0)
    
    return s  # Keep socket open as long as app runs

# ---- Usage ----
lock_socket = singleInstance()


def calculate_max_items():
    """Calculate maximum number of tasks that can fit in the available space"""
    try:
        # Get current window dimensions - force update first
        root.update_idletasks()
        window_height = root.winfo_height()
        
        # If window height is too small (like initial 1), use the geometry setting
        if window_height < 100:
            # Extract height from geometry string like "1400x900"
            geometry = root.geometry()
            if 'x' in geometry:
                window_height = int(geometry.split('x')[1].split('+')[0])
            else:
                window_height = 900  # fallback
        
        print(f"Window height: {window_height}")  # Debug
        
        # Conservative measurements - slightly larger to ensure we don't cut off
        header_height = 100   # High frame with buttons (increased)
        toolbar_height = 90   # Toolbar with run controls (increased)
        task_header_height = 45  # Column headers in tasks frame (increased)
        margins_padding = 100    # Various margins, padding, and spacing (increased)
        task_row_height = 35     # Actual height per task row (back to original)
        
        # Calculate available height for task rows
        available_height = window_height - header_height - toolbar_height - task_header_height - margins_padding
        
        print(f"Available height: {available_height}")  # Debug
        
        # Calculate number of task rows that fit
        max_task_rows = max(12, int(available_height // task_row_height))  # Minimum 12 tasks (increased)
        
        print(f"Calculated max_task_rows: {max_task_rows}")  # Debug
        
        # Cap at reasonable maximum
        return min(max_task_rows, 35)  # Increased max cap
    except Exception as e:
        print(f"Error in calculate_max_items: {e}")
        return 18  # Fallback to higher default
    
    
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

def get_current_max_items():
    """Get the current maximum items, updating the global if needed"""
    global MAX_ITEMS
    new_max = calculate_max_items()
    if new_max != MAX_ITEMS:
        MAX_ITEMS = new_max
        print(f"Updated MAX_ITEMS to {MAX_ITEMS}")  # Debug info
    return MAX_ITEMS

# Force calculation after window is properly set up
def initialize_max_items():
    """Initialize MAX_ITEMS after window is ready"""
    global MAX_ITEMS
    root.update_idletasks()  # Ensure window is drawn
    MAX_ITEMS = calculate_max_items()
    print(f"Initialized MAX_ITEMS to {MAX_ITEMS}")

# Call this after the window setup

# Also add a manual override function for testing
def force_max_items(num_items):
    """Force MAX_ITEMS to a specific number for testing"""
    global MAX_ITEMS
    MAX_ITEMS = num_items
    print(f"Forced MAX_ITEMS to {MAX_ITEMS}")
    if selectedGroup:
        onClick("Select Group")

# You can call this from console: force_max_items(20)
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

# DPI Awareness for Windows
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

root = tkinter.Tk()

# Get screen dimensions for relative sizing
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Increased window size for better initial display
window_width = min(1400, int(screen_width * 0.9))   # Increased from 1200 and 0.85
window_height = min(900, int(screen_height * 0.9))  # Increased from 800 and 0.85
root.geometry(f"{window_width}x{window_height}")

# Make window resizable but set minimum size
root.minsize(1200, 700)  # Increased minimum size
root.resizable(True, True)

# Icon handling with fallback
try:
    icon_path = Path("data") / "VN.ico"
    if icon_path.exists():
        root.iconbitmap(icon_path)
except Exception as e:
    print(f"Could not load icon: {e}")

root.title("TaskFlow")

centerWin(root)
fontStyle = ("Times New Roman", "Segoe UI", "Arial", "Helvetica", "sans-serif")  # Font fallback list
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
                selection = tasksListBox.curselection()
                if not selection:
                    if len(taskGroups) > 0:
                        tasksListBox.selection_set(0)
                        selection = (0,)
                    else:
                        return

                goodGroup = lambda group: group.title.lower().startswith(searchEntryVar.get().lower())
                filteredGroups = list(filter(goodGroup, taskGroups))

                if selection[0] >= len(filteredGroups):
                    return

                for widget in chosenGroupFrame.winfo_children():
                    widget.destroy()

                selectedGroup = filteredGroups[selection[0]]
                size = len(selectedGroup.tasks)
                current_max = get_current_max_items()
                
                # Fix the display start index calculation
                if displayStartIndex >= size:
                    displayStartIndex = max(0, size - current_max)
                elif displayStartIndex + current_max > size:
                    displayStartIndex = max(0, size - current_max)

                # Calculate proper left up/down values
                leftUp = displayStartIndex
                leftDown = max(0, size - displayStartIndex - current_max)

                displaySelected(leftUp=leftUp, leftDown=leftDown)
            
            case "Import Group":
                filePath = filedialog.askopenfilename(
                    title="Choose .task file",
                    filetypes=[("Task file", "*.task")]
                )
                print(color("Chose to open file:", "blue"), 
                    filePath if filePath else None)
                
                if filePath:
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
                    times = int(times_str)
                    if times <= 0:
                        raise ValueError("Times must be positive")
                    
                    for _ in range(times):
                        for task in selectedGroup.tasks:
                            task["run"].invoke()
                            
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
                    onClick("Select Group")

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
                moved = False
                try:
                    if overlay:
                        overlay.closeApp()
                    overlay = SimpleCircleOverlay(screenshotPath="screenshot.jpg", screenshotPathCircle="screenshotC.jpg", wantClickInfo=75)
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
                    alert(f"Error in coords detector. Did you click Done ?\n {e}")
                    root.deiconify()
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
                    if task["changed"]:
                        save_response = tkinter.messagebox.askyesno(
                            "Save Changes", 
                            f"Save changes in {task.desc}?"
                        )
                        if save_response:
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
                    if not all(key in task for key in ["argsEntryVar", "commandMenuVar", "descEntryVar", "timesEntryVar"]):
                        alert("Task not properly initialized")
                        return
                        
                    params = " ".join(
                        task["argsEntryVar"].get().replace(" ", "[SPACE]").split(",")
                    )
                    command = task["commandMenuVar"].get()
                    desc = task["descEntryVar"].get()
                    times_str = task["timesEntryVar"].get()
                    
                    try:
                        times = int(times_str) if times_str.strip() else 1
                        if times <= 0:
                            times = 1
                    except ValueError:
                        times = 1

                    newTask = Task("  ".join([command, params, str(times), desc]))
                    task.update(newTask, False)
                    selectedGroup.saveAt(filePaths[selectedGroup])
                    
                    if "save" in task:
                        task["save"].config(bg="#2196F3")
                        task["changed"] = False

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
                        task["changed"] = True
                    except Exception as e:
                        print(f"Error updating save button color: {e}")

            case b if b.startswith("⬆"):
                if displayStartIndex > 0:
                    displayStartIndex = max(0, displayStartIndex - 1)
                    onClick("Select Group")

            case b if b.startswith("⬇"):
                if selectedGroup:
                    current_max = get_current_max_items()
                    max_start = max(0, len(selectedGroup.tasks) - current_max)
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
                    feedBackWindow.transient(root)
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
                                        bg="#2d2d44", fg="white", font=(fontStyle[0], 14, "bold"),
                                        pady=10)
                    header.pack(fill="x")
                    
                    # Main content frame
                    content_frame = tkinter.Frame(feedBackWindow, bg="#1e1e2f")
                    content_frame.pack(fill="both", expand=True, padx=15, pady=(10, 0))
                    
                    # Feedback text
                    textBox = tkinter.Text(content_frame, height=5, wrap="word",
                                        bg="#f0f0f0", fg="#000000",
                                        relief="flat", highlightthickness=1, highlightbackground="#4cc9f0")
                    textBox.pack(fill="both", expand=True, pady=(0, 8))
                    
                    # Add files button
                    selectBtn = tkinter.Button(content_frame, text="📎 Add files", command=selectFiles,
                                            bg="#4cc9f0", fg="white", activebackground="#3bb0d8",
                                            relief="flat", font=(fontStyle[0], 10, "bold"))
                    selectBtn.pack(fill="x", pady=(0, 5))
                    
                    # Helper text
                    helpText = tkinter.Label(content_frame, text="Double-click a file to remove it",
                                            bg="#1e1e2f", fg="#888888", font=(fontStyle[0], 9))
                    helpText.pack(anchor="w", pady=(0, 3))
                    
                    # Scrollable file list with fixed height
                    fileFrame = tkinter.Frame(content_frame, bg="#1e1e2f")
                    fileFrame.pack(fill="x", pady=(0, 8))
                    
                    fileScroll = tkinter.Scrollbar(fileFrame, orient="vertical")
                    fileListBox = tkinter.Listbox(fileFrame, yscrollcommand=fileScroll.set,
                                                bg="white", fg="black", relief="flat",
                                                selectbackground="#4cc9f0", activestyle="none",
                                                height=6)
                    fileListBox.pack(side="left", fill="both", expand=True)
                    fileScroll.pack(side="right", fill="y")
                    fileScroll.config(command=fileListBox.yview)
                    
                    # Bind double-click event to the listbox
                    fileListBox.bind("<Double-Button-1>", onDoubleClick)
                    
                    # Fixed bottom button frame
                    bottom_frame = tkinter.Frame(feedBackWindow, bg="#1e1e2f")
                    bottom_frame.pack(fill="x", pady=10)
                    
                    sendBtn = tkinter.Button(bottom_frame, text="📤 Send Feedback", command=send,
                                            bg="#72efdd", fg="#000", activebackground="#56d8c9",
                                            relief="flat", font=(fontStyle[0], 11, "bold"))
                    sendBtn.pack(fill="x", padx=15)
                    
                    updateFileList()
                    # Check if logs.txt exists before adding it
                    if os.path.exists("logs.txt"):
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

def normalizeEmail(email, maxLen=35):
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

# Configure root window for responsive design
root.grid_rowconfigure(0, weight=0)  # High frame - fixed
root.grid_rowconfigure(1, weight=1)  # Main content - expandable
root.grid_columnconfigure(0, weight=1)

# High Frame - using grid instead of pack for better control
highFrameBg = "violet"
highFrame = tkinter.Frame(root, bg=highFrameBg)
highFrame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

# Configure high frame grid
for i in range(6):
    highFrame.grid_columnconfigure(i, weight=0)
highFrame.grid_columnconfigure(1, weight=1)  # Email label expands

version = str(getSetting("version"))[:3]

taskFlowButton = MyButton(
    highFrame, 
    text="TaskFlow v" + version, 
    borderwidth=0, font=(fontStyle[0], 22, "bold"), 
    bg=highFrameBg, fg="white",
    anchor="w", justify="center"
)
taskFlowButton.grid(row=0, column=0, pady=5, padx=(15, 10), sticky="w")

email = getSetting("email")
normalizedEmail = normalizeEmail(email)

userLabel = tkinter.Label(
    highFrame, 
    text=normalizedEmail,
    font=('Courier', 13, 'bold'),
    bg=highFrameBg, fg="green",
    anchor="w"
)
userLabel.grid(row=0, column=1, pady=5, padx=(8, 20), sticky="ew")

feedBackButton = MyButton(highFrame, text="FeedBack",
                          bg="blue", fg="white",
                          font=(fontStyle[0], 14), borderwidth=3)
feedBackButton.grid(row=0, column=2, padx=5, pady=2)

newGroupButton = MyButton(highFrame, text="New Group",
                         bg="orange", fg="white",
                         font=(fontStyle[0], 14), borderwidth=3)
newGroupButton.grid(row=0, column=3, padx=5, pady=2)

importGroupButton = MyButton(highFrame, text="Import Group",
                            bg="green", fg="white",
                            font=(fontStyle[0], 14), borderwidth=3)
importGroupButton.grid(row=0, column=4, padx=5, pady=2)

buyCoffeeButton = MyButton(highFrame, text="☕ Buy me a coffee",
                          font=(fontStyle[0], 14, "bold"),
                          borderwidth=3, fg="black", 
                          bg="yellow")
buyCoffeeButton.grid(row=0, column=5, padx=(5, 15), pady=2)

# Main TasksFrame - using grid for better layout control
groupTasksFrame = tkinter.Frame(root, bg="lightgray")
groupTasksFrame.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))

# Configure main frame grid
groupTasksFrame.grid_rowconfigure(0, weight=1)
groupTasksFrame.grid_columnconfigure(0, weight=0)  # Task list - fixed width
groupTasksFrame.grid_columnconfigure(1, weight=1)  # Chosen group - expandable

# Task List Frame
taskListFrame = tkinter.Frame(groupTasksFrame, bg="lightblue")
taskListFrame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

taskListFrame.grid_rowconfigure(1, weight=1)  # Listbox expands
taskListFrame.grid_columnconfigure(0, weight=1)

searchEntryVar = tkinter.StringVar()

searchFrame = tkinter.Frame(taskListFrame)
searchFrame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
searchFrame.grid_columnconfigure(0, weight=1)

searchEntry = tkinter.Entry(
    searchFrame,
    font=(fontStyle[0], 16, "bold"),
    fg="#333333",
    bg="#ffffff",
    insertbackground="#555555",
    relief="flat",                    
    highlightthickness=2,           
    highlightbackground="#cccccc",    
    highlightcolor="#0078d7",
    textvariable=searchEntryVar  
)
searchEntry.grid(row=0, column=0, sticky="ew", padx=(0, 5))

deleteGroupButton = MyButton(
    searchFrame,
    text="🗙",
    justify="center",
    bg="red",
    width=4
)
deleteGroupButton.grid(row=0, column=1)

# Listbox Frame with Scrollbar
listFrame = tkinter.Frame(taskListFrame)
listFrame.grid(row=1, column=0, sticky="nsew")
listFrame.grid_rowconfigure(0, weight=1)
listFrame.grid_columnconfigure(0, weight=1)

tasksListBox = tkinter.Listbox(
    listFrame, bg="orange",
    fg="black",
    selectbackground="gray",
    font=(fontStyle[0], 20, "bold"),
    exportselection=False
)

scrollbar = tkinter.Scrollbar(listFrame, command=tasksListBox.yview)
tasksListBox.configure(yscrollcommand=scrollbar.set)

tasksListBox.bind('<Double-Button-1>', 
                  lambda event: onClick("DoubleClick Group"))
tasksListBox.bind('<<ListboxSelect>>', lambda _: onClick("Select Group"))

tasksListBox.grid(row=0, column=0, sticky="nsew")
scrollbar.grid(row=0, column=1, sticky="ns")

loadGroups()

# Chosen Group Frame - now responsive
chosenGroupFrame = tkinter.Frame(groupTasksFrame, bg="blue")
chosenGroupFrame.grid(row=0, column=1, sticky="nsew")
chosenGroupFrame.grid_rowconfigure(1, weight=1)  # Tasks area expands
chosenGroupFrame.grid_columnconfigure(0, weight=1)

def displaySelected(leftUp=0, leftDown=0):
    global runGroupTimesEntry, displayStartIndex
    toolBarFrameBg = "cyan"
    current_max = get_current_max_items()
    
    print(f"Display: total tasks={len(selectedGroup.tasks)}, max_items={current_max}, start_index={displayStartIndex}")  # Debug
    
    # Clear existing widgets
    for widget in chosenGroupFrame.winfo_children():
        widget.destroy()
    
    toolBarFrame = tkinter.Frame(chosenGroupFrame, bg=toolBarFrameBg)
    toolBarFrame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
    
    # Configure toolbar grid
    for i in range(8):  # Increased for status label
        toolBarFrame.grid_columnconfigure(i, weight=0)
    toolBarFrame.grid_columnconfigure(0, weight=1)  # Author label expands
    
    authorLabel = tkinter.Label(
        toolBarFrame,
        text=f"By {normalizeEmail(selectedGroup.author)}",
        bg="cyan",
        fg="navy",
        font=('Courier', 13, 'bold'),
        anchor="w",
    )
    authorLabel.grid(row=0, column=0, sticky="ew", padx=(10, 20), pady=2)
    
    # Share
    shareButton = MyButton(
        toolBarFrame,
        text="Share",
        bg="green",
        fg="white",
        font=(fontStyle[0], 16, "bold"),
        relief="raised",
        borderwidth=3
    )
    shareButton.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
    
    # Run
    runGroupButton = MyButton(
        toolBarFrame,
        text="Run Group",
        bg="red",
        fg="white",
        font=(fontStyle[0], 16, "bold"),
        relief="raised",
        borderwidth=3
    )
    runGroupButton.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
    
    # Times Entry
    runGroupTimesEntry = tkinter.Entry(
        toolBarFrame,
        width=3,
        font=(fontStyle[0], 22, "bold"),
        bg="white",
        fg="blue",
        justify="center"
    )
    runGroupTimesEntry.insert(0, "1")
    runGroupTimesEntry.grid(row=0, column=3, padx=3, pady=5)
    
    timesLabel = tkinter.Label(
        toolBarFrame,
        font=(fontStyle[0], 20, "bold"),
        bg=toolBarFrameBg,
        text="time(s)"
    )
    timesLabel.grid(row=0, column=4, padx=(2, 5), pady=5)
    
    # Calculate accurate navigation counts and status
    total_tasks = len(selectedGroup.tasks)
    showing_from = displayStartIndex + 1 if total_tasks > 0 else 0
    showing_to = min(displayStartIndex + current_max, total_tasks)
    
    # Navigation buttons with accurate counts
    upButton = MyButton(
        toolBarFrame,
        text=f"⬆{leftUp}" if leftUp > 0 else "⬆",
        bg="yellow" if leftUp > 0 else "lightgray",
        fg="black" if leftUp > 0 else "gray",
        font=(fontStyle[0], 17, "bold"),
        state="normal" if leftUp > 0 else "disabled"
    )
    upButton.grid(row=0, column=5, padx=2, pady=5)
    
    downButton = MyButton(
        toolBarFrame,
        text=f"⬇{leftDown}" if leftDown > 0 else "⬇",
        bg="yellow" if leftDown > 0 else "lightgray",
        fg="black" if leftDown > 0 else "gray",
        font=(fontStyle[0], 17, "bold"),
        state="normal" if leftDown > 0 else "disabled"
    )
    downButton.grid(row=0, column=6, padx=2, pady=5)
    
    # Add status label showing current view
    statusLabel = tkinter.Label(
        toolBarFrame,
        text=f"Showing {showing_from}-{showing_to} of {total_tasks}",
        bg=toolBarFrameBg,
        fg="navy",
        font=(fontStyle[0], 10, "bold")
    )
    statusLabel.grid(row=0, column=7, padx=(10, 5), pady=5)

    # Tasks frame with proper scrollable area
    tasksFrame = tkinter.Frame(chosenGroupFrame, bg="blue")
    tasksFrame.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
    
    # Configure grid columns for the tasks frame
    headers = ["Command", "Description", "Arguments", "Times", "Run", "Save", "Del", "Add"]
    for i, header in enumerate(headers):
        tasksFrame.grid_columnconfigure(i, weight=1 if i == 1 else 0, minsize=80)
        
        headerLabel = tkinter.Label(
            tasksFrame,
            text=header,
            bg="darkgray",
            fg="white",
            font=(fontStyle[0], 12, "bold"),
            relief="raised",
            bd=1
        )
        headerLabel.grid(row=0, column=i, sticky="ew", padx=1, pady=1, ipady=5)
    
    # Add tasks to the grid - show exactly current_max items
    end_index = min(displayStartIndex + current_max, total_tasks)
    visible_tasks = selectedGroup.tasks[displayStartIndex:end_index]
    
    print(f"Showing tasks {displayStartIndex} to {end_index-1} ({len(visible_tasks)} tasks)")  # Debug
    
    for row, task in enumerate(visible_tasks, start=1):
        try:
            command, args = str(task).split("  ")[:2]
            args = ",".join(args.split(" "))
        except (ValueError, IndexError):
            command, args = "WAIT", "1"
        
        # Column 0: OptionMenu for commands
        commandMenuVar = tkinter.StringVar(tasksFrame)
        commandMenuVar.set(command)
        commandMenu = tkinter.OptionMenu(
            tasksFrame,
            commandMenuVar,
            *matchAction.keys(),
            command=lambda varVal, t=task: onClick(varVal, t),
        )
        commandMenu.config(
            font=(fontStyle[0], 12, "bold"),
            relief="solid",
            bd=1,
            fg="violet"
        )
        commandMenu.grid(row=row, column=0, sticky="ew", padx=2, pady=2)
        
        # Column 1: Entry for description
        descEntryVar = tkinter.StringVar()
        descEntry = tkinter.Entry(
            tasksFrame,
            font=(fontStyle[0], 12),
            relief="solid",
            bd=1,
            textvariable=descEntryVar,
        )
        descEntryVar.set(task.desc)
        descEntry.grid(row=row, column=1, sticky="ew", padx=2, pady=2)
        
        # Column 2: Entry for arguments
        argsEntryVar = tkinter.StringVar()
        argsEntry = tkinter.Entry(
            tasksFrame,
            font=(fontStyle[0], 12),
            relief="solid",
            bd=1,
            justify="center",
            textvariable=argsEntryVar
        )
        argsEntryVar.set(args.replace("[SPACE]", " "))
        argsEntry.grid(row=row, column=2, sticky="ew", padx=2, pady=2)
        
        # Column 3: Entry for Times
        timesEntryVar = tkinter.StringVar()
        timesEntry = tkinter.Entry(
            tasksFrame,
            font=(fontStyle[0], 12),
            relief="solid",
            bd=1, 
            justify="center",
            textvariable=timesEntryVar
        )
        timesEntryVar.set(str(task.times))
        timesEntry.grid(row=row, column=3, sticky="ew", padx=2, pady=2)
        
        # Column 4: Run Button
        runTaskBtn = MyButton(
            tasksFrame,
            text="Run",
            font=(fontStyle[0], 12, "bold"),
            bg="#4CAF50",
            fg="white",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=lambda t=task: onClick("Run", t)
        )
        runTaskBtn.grid(row=row, column=4, sticky="ew", padx=2, pady=2)

        # Column 5: Save Button
        saveBtn = MyButton(
            tasksFrame,
            text="Save",
            font=(fontStyle[0], 12, "bold"),
            bg="#2196F3",
            fg="white",
            relief="raised",
            bd=2,
            cursor="hand2",
            command=lambda t=task: onClick("Save", t)
        )
        saveBtn.grid(row=row, column=5, sticky="ew", padx=2, pady=2)
        
        # Column 6: Delete Button
        delButton = MyButton(
            tasksFrame, 
            text="❌",
            bg="red",
            borderwidth=2,
            cursor="hand2",
            command=lambda t=task: onClick("❌", t)
        )
        delButton.grid(row=row, column=6, sticky="ew", padx=2, pady=2)
        
        # Column 7: Add Button
        addDownButton = MyButton(
            tasksFrame, 
            text="➕",
            bg="gray",
            borderwidth=2,
            cursor="hand2",
            command=lambda t=task: onClick("➕", t)
        )
        addDownButton.grid(row=row, column=7, sticky="ew", padx=2, pady=2)

        # Update task dictionary with UI elements
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
                "timesEntryVar": timesEntryVar,
                "changed": False
            }
        )

        # Bind change events to mark task as modified
        commandMenuVar.trace_add("write", lambda *_, t=task: onClick("modify", t))
        descEntryVar.trace_add("write", lambda *_, t=task: onClick("modify", t))
        argsEntryVar.trace_add("write", lambda *_, t=task: onClick("modify", t))
        timesEntryVar.trace_add("write", lambda *_, t=task: onClick("modify", t))

# Search handling
def on_search_change(*args):
    try:
        global displayStartIndex
        displayStartIndex = 0  # Reset to top when searching
        loadGroups()
    except Exception as e:
        print(f"Search error: {e}")

searchEntryVar.trace_add("write", on_search_change)

# Bind window resize events for responsive behavior
def on_window_configure(event):
    if event.widget == root and selectedGroup:
        # Small delay to ensure window sizing is complete
        root.after(100, lambda: refresh_display_if_needed())

def refresh_display_if_needed():
    """Refresh display only if MAX_ITEMS changed significantly"""
    global MAX_ITEMS
    old_max = MAX_ITEMS
    new_max = get_current_max_items()
    
    # Only refresh if the change is significant (more than 2 items difference)
    if abs(new_max - old_max) > 2:
        print(f"Significant resize detected: {old_max} -> {new_max}")
        onClick("Select Group")

root.bind("<Configure>", on_window_configure)

# Center window and show
centerWin(root)
root.after(100, initialize_max_items)  # Small delay to ensure window is ready
root.mainloop()