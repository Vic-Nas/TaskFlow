
import tkinter as tk
from tkinter import font as tkfont


def centerWin(window):
    """
    Centers a tkinter window on the screen.
    
    Args:
        window: The Tk() or Toplevel() object to center
    """
    # Update the window to ensure dimensions are calculated
    window.update_idletasks()
    
    # Get window dimensions
    window_width = window.winfo_width()
    window_height = window.winfo_height()
    
    # If dimensions are 1x1 (not yet configured), use requested geometry
    if window_width <= 1 or window_height <= 1:
        # Parse current geometry (e.g., "500x400+0+0")
        geometry = window.geometry()
        if 'x' in geometry and '+' in geometry:
            size_part = geometry.split('+')[0]
            window_width, window_height = map(int, size_part.split('x'))
        else:
            # Default values if parsing fails
            window_width, window_height = 300, 200
    
    # Get screen dimensions
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    
    # Calculate position to center
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    
    # Apply new position
    window.geometry(f"{window_width}x{window_height}+{x}+{y}")


import tkinter as tk
from tkinter import font as tkfont

def centerWin(window):
    window.update_idletasks()
    windowWidth = window.winfo_width()
    windowHeight = window.winfo_height()

    if windowWidth <= 1 or windowHeight <= 1:
        geometry = window.geometry()
        if 'x' in geometry and '+' in geometry:
            sizePart = geometry.split('+')[0]
            windowWidth, windowHeight = map(int, sizePart.split('x'))
        else:
            windowWidth, windowHeight = 300, 200

    screenWidth = window.winfo_screenwidth()
    screenHeight = window.winfo_screenheight()

    x = (screenWidth - windowWidth) // 2
    y = (screenHeight - windowHeight) // 2

    window.geometry(f"{windowWidth}x{windowHeight}+{x}+{y}")

def alert(content, headings = None, bg = "#222", fg = "#fff", title = "Info", sectionBg = "#333", sectionFg = "#0ff"):
    # Create root but keep it hidden
    root = tk.Tk()
    root.withdraw()
    
    win = tk.Toplevel(root)
    win.title(title)
    win.configure(bg = bg)
    win.resizable(False, False)
    
    sectionFont = tkfont.Font(family = "Helvetica", size = 12, weight = "bold")
    textFont = tkfont.Font(family = "Helvetica", size = 10)

    if isinstance(content, str):
        tk.Label(win, text = content, bg = bg, fg = fg, font = textFont, justify = "left", wraplength = 400).pack(padx = 20, pady = 20)
    elif isinstance(content, list):
        for i, txt in enumerate(content):
            if headings and i < len(headings):
                secTitle = headings[i]
            else:
                secTitle = f"Section {i + 1}:"
            
            tk.Label(win, text = secTitle, bg = sectionBg, fg = sectionFg, font = sectionFont, anchor = "w").pack(fill = "x", padx = 10, pady = (10, 0))
            tk.Label(win, text = txt, bg = bg, fg = fg, font = textFont, justify = "left", wraplength = 400).pack(padx = 20, pady = 5)
    else:
        raise TypeError("content must be a string or a list of strings")
    
    def closeWin(event = None):
        win.destroy()
        root.quit()  # ⬅ force sortie de mainloop
    
    okButton = tk.Button(win, text = "OK", command = closeWin, bg = "#555", fg = "#fff", activebackground = "#777", relief = "flat")
    okButton.pack(pady = 10)

    win.bind("<Return>", closeWin)  # ⬅ Enter valide aussi
    
    centerWin(win)
    win.grab_set()
    root.mainloop()  # mainloop sur root, pas sur win
    root.destroy()   # nettoie complètement