import tkinter as tk
from tkinter import ttk
import threading
import time

class CircleOverlay:
    def __init__(self):
        # Main window setup
        self.root = tk.Tk()
        self.root.title("Circle Overlay Control")
        self.root.geometry("300x150")
        self.root.attributes("-topmost", True)  # Always on top
        
        # Circle properties
        self.radius = 50
        self.circle_x = 400
        self.circle_y = 300
        
        # Create overlay window
        self.overlay = tk.Toplevel(self.root)
        self.setup_overlay()
        
        # Create control interface
        self.setup_controls()
        
        # Start coordinate update thread
        self.running = True
        self.update_thread = threading.Thread(target=self.update_coordinates, daemon=True)
        self.update_thread.start()
        
        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_overlay(self):
        """Setup the transparent overlay window"""
        self.overlay.attributes("-fullscreen", True)
        self.overlay.attributes("-topmost", True)
        self.overlay.attributes("-alpha", 0.7)  # Semi-transparent
        self.overlay.config(bg='black')
        self.overlay.attributes("-transparentcolor", "black")  # Make black transparent
        
        # Create canvas for drawing
        self.canvas = tk.Canvas(
            self.overlay, 
            highlightthickness=0, 
            bg='black',
            width=self.overlay.winfo_screenwidth(),
            height=self.overlay.winfo_screenheight()
        )
        self.canvas.pack(fill="both", expand=True)
        
        # Bind mouse movement
        self.canvas.bind("<Motion>", self.update_circle_position)
        self.canvas.bind("<Button-1>", self.update_circle_position)  # Click to update
    
    def setup_controls(self):
        """Setup the control window interface"""
        # Radius controls
        radius_frame = ttk.Frame(self.root)
        radius_frame.pack(pady=10)
        
        ttk.Label(radius_frame, text="Radius:").pack(side="left")
        
        ttk.Button(radius_frame, text="-", command=self.decrease_radius, width=3).pack(side="left", padx=2)
        
        self.radius_var = tk.StringVar(value=str(self.radius))
        ttk.Label(radius_frame, textvariable=self.radius_var, width=5).pack(side="left", padx=5)
        
        ttk.Button(radius_frame, text="+", command=self.increase_radius, width=3).pack(side="left", padx=2)
        
        # Coordinates display
        coord_frame = ttk.Frame(self.root)
        coord_frame.pack(pady=10)
        
        ttk.Label(coord_frame, text="Coordinates:").pack()
        self.coord_var = tk.StringVar(value=f"X: {self.circle_x}, Y: {self.circle_y}")
        ttk.Label(coord_frame, textvariable=self.coord_var, font=("Arial", 12, "bold")).pack()
        
        # Instructions
        ttk.Label(self.root, text="Move mouse to position circle", 
                 font=("Arial", 8)).pack(pady=5)
    
    def update_circle_position(self, event):
        """Update circle position based on mouse"""
        self.circle_x = event.x
        self.circle_y = event.y
        self.draw_circle()
    
    def draw_circle(self):
        """Draw the circle on the overlay"""
        self.canvas.delete("circle")  # Remove previous circle
        
        # Draw circle outline
        x1 = self.circle_x - self.radius
        y1 = self.circle_y - self.radius
        x2 = self.circle_x + self.radius
        y2 = self.circle_y + self.radius
        
        self.canvas.create_oval(x1, y1, x2, y2, 
                               outline="red", width=2, tags="circle")
        
        # Draw center point
        self.canvas.create_oval(self.circle_x-3, self.circle_y-3, 
                               self.circle_x+3, self.circle_y+3,
                               fill="red", outline="red", tags="circle")
    
    def increase_radius(self):
        """Increase circle radius"""
        self.radius = min(self.radius + 10, 200)  # Max radius 200
        self.radius_var.set(str(self.radius))
        self.draw_circle()
    
    def decrease_radius(self):
        """Decrease circle radius"""
        self.radius = max(self.radius - 10, 10)  # Min radius 10
        self.radius_var.set(str(self.radius))
        self.draw_circle()
    
    def update_coordinates(self):
        """Update coordinate display in real-time"""
        while self.running:
            try:
                self.coord_var.set(f"X: {self.circle_x}, Y: {self.circle_y}")
                time.sleep(0.1)  # Update 10 times per second
            except:
                break
    
    def on_closing(self):
        """Handle application closing"""
        self.running = False
        self.overlay.destroy()
        self.root.destroy()
    
    def run(self):
        """Start the application"""
        # Draw initial circle
        self.draw_circle()
        self.root.mainloop()

# Run the application
if __name__ == "__main__":
    app = CircleOverlay()
    app.run()