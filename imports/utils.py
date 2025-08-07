


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