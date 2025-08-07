
from json import dump, load
import tkinter
from imports.mail import sendVerifiMail
from imports.utils import centerWin

from pymsgbox import alert
from random import randbytes
from pathlib import Path


email = ""

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

def setSetting(key, val):
    with open(Path("data")/"settings.json") as file:
        setting = load(file)
    setting[key] = val
    with open(Path("data")/"settings.json", "w") as file:
        dump(setting, file, indent = 4)


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
        alert("You are logged in.")
        print("\tIt is.")
        setSetting("email", email)
        win.destroy()
        

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
    
    
    logo = logoGen(200, 200)    
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
    