import tkinter as tk
from pymsgbox import alert
from pyautogui import screenshot

class SimpleCircleOverlay:
    def __init__(self, screenshotPath = None):
        self.resultCoords = None
        self.screenshotPath = screenshotPath
        
        # Create transparent overlay window
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.7)
        self.root.config(bg='black')
        self.root.attributes("-transparentcolor", "black")
        
        # Circle properties
        self.radius = 20
        self.x = 400
        self.y = 300
        
        # Drag properties
        self.dragging = False
        self.dragStartX = 0
        self.dragStartY = 0
        
        # Create canvas
        self.canvas = tk.Canvas(self.root, highlightthickness=0, bg='black')
        self.canvas.pack(fill="both", expand=True)
        
        # Create coordinate label frame (better visibility)
        self.labelFrame = tk.Frame(self.root, bg="darkgray", relief="raised", bd=2)
        self.coordLabel = tk.Label(
            self.labelFrame, 
            text=f"X: {self.x}, Y: {self.y}",
            fg="white", 
            bg="darkgray",
            font=("Arial", 12, "bold"),
            padx=10, pady=5
        )
        self.coordLabel.pack(side="left")
        
        # Done button
        self.doneButton = tk.Button(
            self.labelFrame,
            text="Done",
            fg="white",
            bg="green",
            font=("Arial", 12, "bold"),
            command=self.doneSelection,
            padx=10,
            height=1,
            bd=0
        )
        self.doneButton.pack(side="left", padx=5)
        
        # Close button (X)
        self.closeButton = tk.Button(
            self.labelFrame,
            text="X",
            fg="white",
            bg="red",
            font=("Arial", 12, "bold"),
            command=self.closeApp,
            width=3,
            height=1,
            bd=0
        )
        self.closeButton.pack(side="right", padx=5)
        
        # Position label frame in top-center for better visibility
        self.labelFrame.place(relx=0.5, y=10, anchor="n")
        
        # Bind mouse events for dragging
        self.canvas.bind("<Button-1>", self.startDrag)
        self.canvas.bind("<B1-Motion>", self.dragCircle)
        self.canvas.bind("<ButtonRelease-1>", self.stopDrag)
        
        # Bind Escape key to close
        self.root.bind("<Escape>", lambda e: self.closeApp())
        
        # Make window click-through except for interactive elements
        self.root.wm_attributes("-transparentcolor", "black")
        
        # Draw initial circle
        self.drawCircle()

    def startDrag(self, event):
        # Check if click is within circle (much larger tolerance)
        distance = ((event.x - self.x)**2 + (event.y - self.y)**2)**0.5
        if distance <= self.radius + 10:  # Much larger tolerance area
            self.dragging = True
            self.dragStartX = event.x - self.x
            self.dragStartY = event.y - self.y
            self.canvas.config(cursor="hand2")
            print(f"Started dragging at {event.x}, {event.y}")  # Debug
    
    def dragCircle(self, event):
        if self.dragging:
            self.x = event.x - self.dragStartX
            self.y = event.y - self.dragStartY
            self.coordLabel.config(text=f"X: {self.x}, Y: {self.y}")
            self.drawCircle()
            print(f"Dragging to {self.x}, {self.y}")  # Debug
    
    def stopDrag(self, event):
        if self.dragging:
            print("Stopped dragging")  # Debug
        self.dragging = False
        self.canvas.config(cursor="")

    def drawCircle(self):
        self.canvas.delete("circle")
        
        # Circle outline (make it more visible)
        x1, y1 = self.x - self.radius, self.y - self.radius
        x2, y2 = self.x + self.radius, self.y + self.radius
        self.canvas.create_oval(x1, y1, x2, y2, outline="red", width=3, tags="circle")
        
        # Center point
        self.canvas.create_oval(self.x-3, self.y-3, self.x+3, self.y+3,
                               fill="red", tags="circle")
        
        # Add large invisible clickable area for easier dragging
        self.canvas.create_oval(self.x-self.radius-15, self.y-self.radius-15, 
                               self.x+self.radius+15, self.y+self.radius+15,
                               outline="", fill="", tags="circle")
    
    def doneSelection(self):
        self.resultCoords = (self.x, self.y)
        if self.screenshotPath:
            screenshot(self.screenshotPath)
        self.closeApp()
    
    def closeApp(self):
        try:
            self.root.quit()
        except:
            pass
        try:
            self.root.destroy()
        except:
            pass

    def run(self):
            
        alert("Click and drag the circle to move it.")
        self.root.mainloop()
        
        # Return coordinates if Done was clicked
        if self.resultCoords:
            return self.resultCoords
        else:
            return None