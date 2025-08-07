import tkinter as tk
import math

class ScreenCircleTracker:
    def __init__(self):
        # Create transparent overlay window
        self.root = tk.Tk()
        self.root.title("Circle Tracker")
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Configure window to cover entire screen
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")
        self.root.overrideredirect(True)  # Remove window borders
        self.root.attributes('-topmost', True)  # Always on top
        self.root.attributes('-alpha', 0.3)  # Semi-transparent
        self.root.configure(bg='black')
        
        # Create canvas covering entire screen
        self.canvas = tk.Canvas(
            self.root, 
            bg='black', 
            highlightthickness=0,
            width=screen_width,
            height=screen_height
        )
        self.canvas.pack()
        
        # Circle properties
        self.circle_radius = 30
        self.circle_x = screen_width // 2
        self.circle_y = screen_height // 2
        self.circle_id = None
        self.label_id = None
        
        # Control panel window (separate, opaque window)
        self.control_window = tk.Toplevel(self.root)
        self.control_window.title("Controls")
        self.control_window.geometry("250x120+50+50")
        self.control_window.attributes('-topmost', True)
        self.control_window.configure(bg='darkgray')
        
        # Control labels
        self.coord_label = tk.Label(
            self.control_window, 
            text="Coordinates: (0, 0)",
            font=('Arial', 10, 'bold'),
            bg='darkgray', fg='white'
        )
        self.coord_label.pack(pady=5)
        
        self.radius_label = tk.Label(
            self.control_window,
            text=f"Radius: {self.circle_radius}",
            font=('Arial', 10, 'bold'),
            bg='darkgray', fg='white'
        )
        self.radius_label.pack(pady=5)
        
        # Control buttons
        button_frame = tk.Frame(self.control_window, bg='darkgray')
        button_frame.pack(pady=5)
        
        tk.Button(button_frame, text="R+", command=lambda: self.adjust_radius(5)).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="R-", command=lambda: self.adjust_radius(-5)).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="Quit", command=self.quit_app, bg='red', fg='white').pack(side=tk.LEFT, padx=2)
        
        # Track dragging
        self.dragging = False
        
        # Bind events to main canvas
        self.canvas.bind('<Button-1>', self.on_click)
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_release)
        self.canvas.bind('<MouseWheel>', self.on_scroll)
        
        # Bind keyboard events
        self.root.bind('<KeyPress>', self.on_key)
        self.root.focus_set()
        
        # Initial draw
        self.draw_circle()
        self.update_labels()
        
    def draw_circle(self):
        # Clear previous circle
        if self.circle_id:
            self.canvas.delete(self.circle_id)
            
        # Draw new circle
        x1 = self.circle_x - self.circle_radius
        y1 = self.circle_y - self.circle_radius
        x2 = self.circle_x + self.circle_radius
        y2 = self.circle_y + self.circle_radius
        
        self.circle_id = self.canvas.create_oval(
            x1, y1, x2, y2,
            outline='red', width=3, fill='', tags='circle'
        )
        
    def update_labels(self):
        # Update coordinate display
        self.coord_label.config(text=f"Coordinates: ({self.circle_x}, {self.circle_y})")
        self.radius_label.config(text=f"Radius: {self.circle_radius}")
        
    def on_click(self, event):
        # Check if click is on circle
        distance = math.sqrt((event.x - self.circle_x)**2 + (event.y - self.circle_y)**2)
        if distance <= self.circle_radius:
            self.dragging = True
            
    def on_drag(self, event):
        if self.dragging:
            self.circle_x = event.x
            self.circle_y = event.y
            self.draw_circle()
            self.update_labels()
            
    def on_release(self, event):
        self.dragging = False
        
    def on_scroll(self, event):
        # Adjust radius with mouse wheel
        delta = 5 if event.delta > 0 else -5
        self.adjust_radius(delta)
        
    def adjust_radius(self, delta):
        new_radius = self.circle_radius + delta
        self.circle_radius = max(10, min(100, new_radius))  # Limit between 10 and 100
        self.draw_circle()
        self.update_labels()
        
    def on_key(self, event):
        if event.keysym == 'Escape':
            self.quit_app()
        elif event.keysym == 'Up':
            self.adjust_radius(5)
        elif event.keysym == 'Down':
            self.adjust_radius(-5)
            
    def quit_app(self):
        self.root.quit()
        self.root.destroy()
        
    def run(self):
        print("Screen Circle Tracker Started!")
        print("Controls:")
        print("- Click and drag red circle to move")
        print("- Mouse wheel or buttons R+/R- to change radius")
        print("- Up/Down arrows also change radius")
        print("- ESC or Quit button to exit")
        print("- Circle is visible everywhere on screen")
        self.root.mainloop()

if __name__ == "__main__":
    tracker = ScreenCircleTracker()
    tracker.run()