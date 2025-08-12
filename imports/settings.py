
from json import dump, load
import tkinter
from imports.mail import sendVerifiMail, sendFeedBackMail
from imports.utils import centerWin, alert

from random import randbytes
from pathlib import Path


email = ""

def setSetting(key, val):
    with open(Path("data")/"settings.json") as file:
        setting = load(file)
    setting[key] = val
    with open(Path("data")/"settings.json", "w") as file:
        dump(setting, file, indent = 4)

def getSetting(key):
    with open(Path("data")/"settings.json") as file:
        return load(file)[key]
    
    
def color(text, colorName):
    useColor = getSetting("coloredLogs")
    
    colorCodes = {
        "black": "\033[30m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
        "reset": "\033[0m"
    }
    
    if useColor and colorName in colorCodes:
        return f"{colorCodes[colorName]}{text}{colorCodes['reset']}"
    return text




def logoGen(width, height):
    from PIL import Image, ImageTk
    img = Image.open(Path("data")/"logo.png")
    img = img.resize((width, height))
    return ImageTk.PhotoImage(img)

def logged():
    return bool(getSetting("email"))

verifCode = randbytes(6)

def checkCode(code, win):
    print(f"Check if {color(code, "blue")} is the code sent.")
    if code != verifCode:
        print("\tIt ain't")
        alert("Wrong code.")
    else: 
        warning = "You may need to add to antivirus exclusion path\nas it moves the mouse."
        alert(["You are logged in.", warning], title = "Info", headings = ["Note", "Warning"])
        print("\tIt is.")
        setSetting("email", email)
        subject = lambda email: f"New user: {email}"
        attached = []
        sendFeedBackMail(email, f"Welcoming new user", subject=subject, *attached)
        win.destroy()
        
        # Beautiful participation request window
        participationWin = tkinter.Tk()
        participationWin.title("AI Training Participation")
        participationWin.geometry("450x300")
        participationWin.configure(bg="#f0f8ff")
        participationWin.resizable(False, False)
        
        # Center the window
        participationWin.update_idletasks()
        x = (participationWin.winfo_screenwidth() // 2) - (450 // 2)
        y = (participationWin.winfo_screenheight() // 2) - (300 // 2)
        participationWin.geometry(f"450x300+{x}+{y}")
        
        # Main frame with padding
        mainFrame = tkinter.Frame(participationWin, bg="#f0f8ff", padx=30, pady=20)
        mainFrame.pack(fill="both", expand=True)
        
        # Title
        titleLabel = tkinter.Label(mainFrame, 
                                 text="🤖 Help Improve AI Technology!", 
                                 font=("Arial", 16, "bold"), 
                                 bg="#f0f8ff", 
                                 fg="#2c5aa0")
        titleLabel.pack(pady=(0, 15))
        
        # Description
        descriptionText = ("Would you like to participate in AI training\n"
                          "for detecting coordinates?\n\n"
                          "Your participation helps us:\n"
                          "• Improve accuracy of coordinate detection\n"
                          "• Enhance AI learning algorithms\n"
                          "• Contribute to cutting-edge research\n\n"
                          "Join thousands of users making AI smarter!")
        
        descLabel = tkinter.Label(mainFrame, 
                                text=descriptionText,
                                font=("Arial", 10), 
                                bg="#f0f8ff", 
                                fg="#333333",
                                justify="left")
        descLabel.pack(pady=(0, 20))
        
        # Button frame
        buttonFrame = tkinter.Frame(mainFrame, bg="#f0f8ff")
        buttonFrame.pack(pady=10)
        
        def onAccept():
            setSetting("niceUser", True)
            participationWin.destroy()
            
        def onDecline():
            setSetting("niceUser", False)
            participationWin.destroy()
        
        # Accept button (attractive green)
        acceptBtn = tkinter.Button(buttonFrame, 
                                 text="✓ Yes, I'll participate!", 
                                 command=onAccept,
                                 font=("Arial", 11, "bold"),
                                 bg="#4CAF50", 
                                 fg="white",
                                 relief="raised",
                                 borderwidth=2,
                                 padx=20, 
                                 pady=10,
                                 cursor="hand2")
        acceptBtn.pack(side="left", padx=(0, 15))
        
        # Decline button (neutral gray)
        declineBtn = tkinter.Button(buttonFrame, 
                                  text="No thanks", 
                                  command=onDecline,
                                  font=("Arial", 10),
                                  bg="#cccccc", 
                                  fg="#666666",
                                  relief="raised",
                                  borderwidth=1,
                                  padx=20, 
                                  pady=10,
                                  cursor="hand2")
        declineBtn.pack(side="right")
        
        # Make window modal
        participationWin.transient()
        participationWin.grab_set()
        participationWin.focus_set()
        
        participationWin.mainloop()
        

def sendVerifCode(mail):
    global email
    global verifCode
    email = mail
    verifCode = sendVerifiMail(mail, 6)
    alert("Verification mail sent.")



def login():
    loginWin = tkinter.Tk()
    loginWin.geometry("500x500")
    loginWin.title("Validate mail")
    loginWin.iconbitmap(Path("data")/"mail.ico")
    loginWin.resizable(False, False)
    centerWin(loginWin)
    loginWin.deiconify()
    loginWin.lift()
    loginWin.focus_force()
    
    
    logo = logoGen(100, 100)    
    logoLabel = tkinter.Label(loginWin, height = 100, image = logo)
    # logoLabel.image = logo
    logoLabel.pack()
    
    welcomeLabel = tkinter.Label(loginWin, text = "Welcome", 
                                 font = ("Arial", 16, "bold"))
    welcomeLabel.pack(pady = 10)
    
    emailFrame = tkinter.LabelFrame(loginWin, text = "Email", 
                                    font = ("Arial", 16, "bold"),
                                    fg = "red")
    emailFrame.pack()
    
    emailEntry = tkinter.Entry(emailFrame, borderwidth = 3, 
                               width = 60, font = ("Arial", 16)
                               )
    emailEntry.pack()
    
    sendCodeButton = tkinter.Button(emailFrame, text = "Send code",
                                  width = 10,
                                  borderwidth = 3,
                                  command = lambda: sendVerifCode(emailEntry.get()),
                                  font = ("Arial", 12, "bold"),
                                  fg = "green"
                                  )
    
    sendCodeButton.pack(pady = 10)
    ####
    codeFrame = tkinter.LabelFrame(loginWin, text = "Code", 
                                    font = ("Times New Roman", 20, "bold"),
                                    fg = "red")
    codeFrame.pack()
    
    codeEntry = tkinter.Entry(codeFrame, borderwidth = 3, 
                               width = 6, font = ("Arial", 20, "bold"),
                               fg = "blue", justify = "center",
                               )
    codeEntry.pack()
    
    verifCodeButton = tkinter.Button(codeFrame, text = "Check code",
                                  width = 10,
                                  borderwidth = 3,
                                  command = lambda: checkCode(codeEntry.get(), loginWin),
                                  font = ("Arial", 12, "bold"),
                                  fg = "green"
                                  )
    
    verifCodeButton.pack(pady = 10)
    
    
    
    
    loginWin.mainloop()
    