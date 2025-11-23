class Geodata:
    def __init__(self, lat: float, lon: float, x: float, y: float):
        self.lat = lat
        self.lon = lon
        self.x = x
        self.y = y

    def __repr__(self):
        return f"Geodata(lat={self.lat}, lon={self.lon}, x={self.x}, y={self.y})"
