
import tkinter as tk

class InteractiveCircle:
    def __init__(self):
        # Create main window
        self.window = tk.Tk()
        self.window.title("Circle with Coordinates")
        self.window.geometry("600x500")
        
        # Variables
        self.radius = 30
        self.circle_x = 300  # Circle center x position
        self.circle_y = 200  # Circle center y position
        
        # Canvas for drawing
        self.canvas = tk.Canvas(self.window, width=600, height=400, bg='white')
        self.canvas.pack(pady=10)
        
        # Label to display coordinates
        self.coords_label = tk.Label(self.window, text="", font=('Arial', 12))
        self.coords_label.pack()
        
        # Scale to modify radius
        self.radius_scale = tk.Scale(self.window, from_=10, to=100, orient=tk.HORIZONTAL,
                                   label="Circle Radius", command=self.change_radius)
        self.radius_scale.set(self.radius)
        self.radius_scale.pack()
        
        # Draw initial circle
        self.draw_circle()
        
        # Bind mouse events
        self.canvas.bind('<Button-1>', self.mouse_click)
        self.canvas.bind('<B1-Motion>', self.mouse_drag)
        
    def draw_circle(self):
        # Clear canvas
        self.canvas.delete("all")
        
        # Draw circle
        x1 = self.circle_x - self.radius
        y1 = self.circle_y - self.radius
        x2 = self.circle_x + self.radius
        y2 = self.circle_y + self.radius
        
        self.canvas.create_oval(x1, y1, x2, y2, fill='lightblue', outline='blue', width=2)
        
        # Update coordinates display
        self.update_coordinates()
    
    def update_coordinates(self):
        coords_text = f"Center: ({self.circle_x}, {self.circle_y}) | Radius: {self.radius}"
        self.coords_label.config(text=coords_text)
    
    def mouse_click(self, event):
        # Move circle to mouse position
        self.circle_x = event.x
        self.circle_y = event.y
        self.draw_circle()
    
    def mouse_drag(self, event):
        # Move circle while dragging
        self.circle_x = event.x
        self.circle_y = event.y
        self.draw_circle()
    
    def change_radius(self, value):
        # Update radius when scale changes
        self.radius = int(value)
        self.draw_circle()
    
    def run(self):
        # Start the application
        self.window.mainloop()

# Create and run the application
if __name__ == "__main__":
    app = InteractiveCircle()
    app.run()