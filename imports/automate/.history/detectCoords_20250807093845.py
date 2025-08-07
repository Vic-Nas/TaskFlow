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
        
        # Create canvas
        self.canvas = tk.Canvas(self.root, highlightthickness=0, bg='black')
        self.canvas.pack(fill="both", expand=True)
        
        # Create coordinate label
        self.coord_label = tk.Label(
            self.root, 
            text=f"X: {self.x}, Y: {self.y}",
            fg="white", 
            bg="black",
            font=("Arial", 14, "bold")
        )
        self.coord_label.place(x=10, y=10)
        
        # Bind mouse movement and click
        self.canvas.bind("<Motion>", self.update_position)
        self.canvas.bind("<Button-1>", self.update_position)
        
        # Bind Escape key to close
        self.root.bind("<Escape>", lambda e: self.root.quit())
        
        # Draw initial circle
        self.draw_circle()
    
    def update_position(self, event):
        """Update circle position and coordinates"""
        self.x = event.x
        self.y = event.y
        self.coord_label.config(text=f"X: {self.x}, Y: {self.y}")
        self.draw_circle()
    
    def draw_circle(self):
        """Draw the circle"""
        self.canvas.delete("circle")
        
        # Circle outline
        x1, y1 = self.x - self.radius, self.y - self.radius
        x2, y2 = self.x + self.radius, self.y + self.radius
        self.canvas.create_oval(x1, y1, x2, y2, outline="red", width=2, tags="circle")
        
        # Center point
        self.canvas.create_oval(self.x-2, self.y-2, self.x+2, self.y+2, 
                               fill="red", tags="circle")
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

# Run the application
if __name__ == "__main__":
    app = SimpleCircleOverlay()
    alert("Move mouse to position circle. Press Escape to close.")
    app.run()