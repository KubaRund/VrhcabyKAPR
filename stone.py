class Stone:
    def __init__(self, color, place_history, deaths):
        self.color = color
        self.deaths = deaths
        self.place_history = place_history

    def __repr__(self):
        if self.color == "W":
            return "□"
        if self.color == "K":
            return "■"


