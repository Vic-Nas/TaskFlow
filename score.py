

def scoreCoords(x, y, centerX = 0, centerY = 0, radius = 20):
    distance = ((x - centerX) ** 2 + (y - centerY) ** 2) ** 0.5
    return max(0, 100 * (1 - distance / radius))