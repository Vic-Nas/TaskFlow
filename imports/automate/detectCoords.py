import tkinter as tk
from pymsgbox import alert

class SimpleCircleOverlay:
    def __init__(self):
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
        self.drag_start_x = 0
        self.drag_start_y = 0
        
        # Create canvas
        self.canvas = tk.Canvas(self.root, highlightthickness=0, bg='black')
        self.canvas.pack(fill="both", expand=True)
        
        # Create coordinate label frame (better visibility)
        self.label_frame = tk.Frame(self.root, bg="darkgray", relief="raised", bd=2)
        self.coord_label = tk.Label(
            self.label_frame, 
            text=f"X: {self.x}, Y: {self.y}",
            fg="white", 
            bg="darkgray",
            font=("Arial", 12, "bold"),
            padx=10, pady=5
        )
        self.coord_label.pack(side="left")
        
        # Close button (X)
        self.close_button = tk.Button(
            self.label_frame,
            text="X",
            fg="white",
            bg="red",
            font=("Arial", 12, "bold"),
            command=self.close_app,
            width=3,
            height=1,
            bd=0
        )
        self.close_button.pack(side="right", padx=5)
        
        # Position label frame in top-center for better visibility
        self.label_frame.place(relx=0.5, y=10, anchor="n")
        
        # Bind mouse events for dragging
        self.canvas.bind("<Button-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag_circle)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drag)
        
        # Bind Escape key to close
        self.root.bind("<Escape>", lambda e: self.close_app())
        
        # Make window click-through except for interactive elements
        self.root.wm_attributes("-transparentcolor", "black")
        
        # Draw initial circle
        self.draw_circle()

    def start_drag(self, event):
        # Check if click is within circle (much larger tolerance)
        distance = ((event.x - self.x)**2 + (event.y - self.y)**2)**0.5
        if distance <= self.radius + 10:  # Much larger tolerance area
            self.dragging = True
            self.drag_start_x = event.x - self.x
            self.drag_start_y = event.y - self.y
            self.canvas.config(cursor="hand2")
            print(f"Started dragging at {event.x}, {event.y}")  # Debug
    
    def drag_circle(self, event):
        if self.dragging:
            self.x = event.x - self.drag_start_x
            self.y = event.y - self.drag_start_y
            self.coord_label.config(text=f"X: {self.x}, Y: {self.y}")
            self.draw_circle()
            print(f"Dragging to {self.x}, {self.y}")  # Debug
    
    def stop_drag(self, event):
        if self.dragging:
            print("Stopped dragging")  # Debug
        self.dragging = False
        self.canvas.config(cursor="")

    def draw_circle(self):
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
    
    def close_app(self):
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