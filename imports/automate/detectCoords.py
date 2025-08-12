import tkinter as tk
from tkinter import messagebox
import os
import tempfile
import base64
import json
from urllib.request import urlopen, Request
from urllib.parse import urlencode

try:
    from pyautogui import screenshot
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    print("Warning: pyautogui not available. Screenshot functionality disabled.")

class SimpleCircleOverlay:
    def __init__(self, screenshotPath=None, screenshotPathCircle=None, wantClickInfo=0, 
                 circleColor="red", circleRadius=20):
        self.resultCoords = None
        self.screenshotPath = screenshotPath
        self.screenshotPathCircle = screenshotPathCircle
        self.wantClickInfo = wantClickInfo
        self.circleColor = circleColor
        self.circleRadius = circleRadius
        
        # Create transparent overlay window
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.7)
        self.root.config(bg='black')
        self.root.attributes("-transparentcolor", "black")
        
        # Circle properties
        self.radius = self.circleRadius
        
        # Drag properties
        self.dragging = False
        self.dragStartX = 0
        self.dragStartY = 0
        
        # Create canvas
        self.canvas = tk.Canvas(self.root, highlightthickness=0, bg='black')
        self.canvas.pack(fill="both", expand=True)
        
        # Center circle on screen
        self.root.update()
        screenWidth = self.root.winfo_screenwidth()
        screenHeight = self.root.winfo_screenheight()
        self.x = screenWidth // 2
        self.y = screenHeight // 2
        self.initialX = self.x
        self.initialY = self.y
        self.moved = False
        
        # Create button frame
        self.labelFrame = tk.Frame(self.root, bg="darkgray", relief="raised", bd=2)
        
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
        
        # OCR status label
        if self.wantClickInfo != 0:
            self.ocrLabel = tk.Label(
                self.labelFrame,
                text="OCR: Web",
                fg="white",
                bg="darkgray",
                font=("Arial", 10)
            )
            self.ocrLabel.pack(side="left", padx=10)
        
        # Close button
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
        
        # Position label frame
        self.labelFrame.place(relx=0.5, y=10, anchor="n")
        
        # Bind mouse events
        self.canvas.bind("<Button-1>", self.startDrag)
        self.canvas.bind("<B1-Motion>", self.dragCircle)
        self.canvas.bind("<ButtonRelease-1>", self.stopDrag)
        
        # Bind Escape key
        self.root.bind("<Escape>", lambda e: self.closeApp())
        
        # Make window click-through
        self.root.wm_attributes("-transparentcolor", "black")
        
        # Draw initial circle
        self.drawCircle()

    def startDrag(self, event):
        distance = ((event.x - self.x)**2 + (event.y - self.y)**2)**0.5
        if distance <= self.radius + 10:
            self.dragging = True
            self.dragStartX = event.x
            self.dragStartY = event.y
            self.startCircleX = self.x
            self.startCircleY = self.y
            self.canvas.config(cursor="hand2")
    
    def dragCircle(self, event):
        if self.dragging:
            deltaX = event.x - self.dragStartX
            deltaY = event.y - self.dragStartY
            
            self.x = self.startCircleX + deltaX
            self.y = self.startCircleY + deltaY
            
            if self.x != self.initialX or self.y != self.initialY:
                self.moved = True
                
            self.drawCircle()
    
    def stopDrag(self, event):
        self.dragging = False
        self.canvas.config(cursor="")

    def drawCircle(self):
        self.canvas.delete("circle")
        
        # Circle outline
        x1, y1 = self.x - self.radius, self.y - self.radius
        x2, y2 = self.x + self.radius, self.y + self.radius
        self.canvas.create_oval(x1, y1, x2, y2, outline=self.circleColor, width=3, tags="circle")
        
        # Center point
        self.canvas.create_oval(self.x-3, self.y-3, self.x+3, self.y+3,
                               fill=self.circleColor, tags="circle")
        
        # Invisible clickable area
        self.canvas.create_oval(self.x-self.radius-15, self.y-self.radius-15, 
                               self.x+self.radius+15, self.y+self.radius+15,
                               outline="", fill="", tags="circle")

    def performWebOcr(self, imagePath):
        """Ultra-lightweight web OCR using built-in urllib only"""
        try:
            # Read and encode image
            with open(imagePath, 'rb') as img_file:
                img_data = base64.b64encode(img_file.read()).decode()
            
            # Use OCR.space free API
            url = 'https://api.ocr.space/parse/image'
            data = {
                'base64Image': f'data:image/png;base64,{img_data}',
                'language': 'eng',
                'isOverlayRequired': 'false',
                'scale': 'true',
                'OCREngine': '2'
            }
            
            # Create request
            postdata = urlencode(data).encode()
            request = Request(url, postdata)
            request.add_header('Content-Type', 'application/x-www-form-urlencoded')
            
            # Make request with timeout
            response = urlopen(request, timeout=15)
            result = json.loads(response.read().decode())
            
            # Parse results
            if result.get('ParsedResults') and len(result['ParsedResults']) > 0:
                parsed_text = result['ParsedResults'][0].get('ParsedText', '').strip()
                
                if parsed_text and not parsed_text.isdigit():
                    # Clean up text and format like original
                    lines = [line.strip() for line in parsed_text.split('\n') if line.strip()]
                    text_results = []
                    
                    for line in lines:
                        if line and not line.isdigit() and len(line) > 1:
                            text_results.append(f"{line},90")  # Use 90% confidence
                    
                    return "+".join(text_results)
            
            return ""
            
        except Exception as e:
            print(f"Web OCR error: {e}")
            return ""

    def captureAndOcr(self):
        """Capture area and perform lightweight web OCR"""
        try:
            if not PYAUTOGUI_AVAILABLE:
                print("Cannot capture screenshot - pyautogui not available")
                return ""
                
            # Hide overlay temporarily
            self.root.withdraw()
            
            # Calculate capture area
            captureRadius = self.wantClickInfo
            left = max(0, self.x - captureRadius)
            top = max(0, self.y - captureRadius)
            right = min(self.root.winfo_screenwidth(), self.x + captureRadius)
            bottom = min(self.root.winfo_screenheight(), self.y + captureRadius)
            
            # Take screenshot
            regionScreenshot = screenshot(region=(left, top, right - left, bottom - top))
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                temp_path = tmp_file.name
                regionScreenshot.save(temp_path)
            
            # Perform web OCR
            ocrData = self.performWebOcr(temp_path)
            
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except:
                pass
            
            # Show overlay again
            self.root.deiconify()
            
            return ocrData
            
        except Exception as e:
            print(f"Error during OCR capture: {e}")
            self.root.deiconify()
            return ""
    
    def doneSelection(self):
        ocrData = ""
        
        # Perform OCR if requested
        if self.wantClickInfo != 0:
            print("Performing OCR... (requires internet)")
            ocrData = self.captureAndOcr()
        
        self.resultCoords = (self.x, self.y, self.moved, ocrData)
        
        # Take screenshots if available
        if PYAUTOGUI_AVAILABLE:
            try:
                if self.screenshotPathCircle:
                    screenshot(self.screenshotPathCircle)
                
                if self.screenshotPath:
                    self.root.withdraw()
                    screenshot(self.screenshotPath)
                    self.root.deiconify()
            except Exception as e:
                print(f"Screenshot error: {e}")
            
        self.closeApp()
    
    def closeApp(self):
        try:
            self.root.quit()
            self.root.destroy()
        except:
            pass

    def run(self):
        print("Ultra-lightweight OCR overlay ready!")
        print("Click and drag the circle to move it. Press Done when finished or Escape to cancel.")
        if self.wantClickInfo != 0:
            print("OCR: Web-based (requires internet connection)")
        
        self.root.mainloop()
        
        if self.resultCoords:
            if self.wantClickInfo != 0:
                return self.resultCoords  # (x, y, moved, ocrData)
            else:
                return (self.resultCoords[0], self.resultCoords[1], self.resultCoords[2])  # (x, y, moved)
        else:
            return None