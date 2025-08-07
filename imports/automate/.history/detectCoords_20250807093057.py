import tkinter as tk
import math

class CircleTracker:
    def __init__(self):
        # Create main window
        self.root = tk.Tk()
        self.root.title("Circle Coordinate Tracker")
        self.root.geometry("800x600")
        self.root.configure(bg='black')
        
        # Make window always on top
        self.root.attributes('-topmost', True)
        
        # Create canvas
        self.canvas = tk.Canvas(self.root, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Circle properties
        self.circle_radius = 20
        self.circle_x = 400
        self.circle_y = 300
        self.circle_id = None
        self.label_id = None
        
        # Track if dragging
        self.dragging = False
        
        # Bind events
        self.canvas.bind('<Button-1>', self.on_click)
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_release)
        self.canvas.bind('<MouseWheel>', self.on_scroll)
        self.canvas.bind('<Configure>', self.on_resize)
        
        # Bind keyboard events for radius adjustment
        self.root.bind('<Up>', lambda e: self.adjust_radius(2))
        self.root.bind('<Down>', lambda e: self.adjust_radius(-2))
        self.root.focus_set()
        
        # Initial draw
        self.draw_circle()
        self.update_label()
        
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
            outline='red', width=2, fill='', tags='circle'
        )
        
    def update_label(self):
        # Clear previous label
        if self.label_id:
            self.canvas.delete(self.label_id)
            
        # Get screen coordinates (for pyautogui)
        screen_x = self.root.winfo_rootx() + self.circle_x
        screen_y = self.root.winfo_rooty() + self.circle_y
        
        # Create label text
        text = f"Coords: ({screen_x}, {screen_y})\nRadius: {self.circle_radius}"
        
        # Position label at top-left corner
        self.label_id = self.canvas.create_text(
            10, 10, text=text, anchor='nw',
            fill='white', font=('Arial', 12, 'bold')
        )
        
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
            self.update_label()
            
    def on_release(self, event):
        self.dragging = False
        
    def on_scroll(self, event):
        # Adjust radius with mouse wheel
        delta = 2 if event.delta > 0 else -2
        self.adjust_radius(delta)
        
    def adjust_radius(self, delta):
        self.circle_radius = max(10, self.circle_radius + delta)
        self.draw_circle()
        self.update_label()
        
    def on_resize(self, event):
        # Keep circle within bounds when window is resized
        canvas_width = event.width
        canvas_height = event.height
        
        self.circle_x = min(max(self.circle_radius, self.circle_x), 
                           canvas_width - self.circle_radius)
        self.circle_y = min(max(self.circle_radius, self.circle_y), 
                           canvas_height - self.circle_radius)
        
        self.draw_circle()
        self.update_label()
        
    def run(self):
        print("Circle Tracker Started!")
        print("Controls:")
        print("- Click and drag circle to move")
        print("- Mouse wheel or Up/Down arrows to change radius")
        print("- Coordinates shown are screen coordinates for pyautogui")
        self.root.mainloop()

if __name__ == "__main__":
    tracker = CircleTracker()
    tracker.run()