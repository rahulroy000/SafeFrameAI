
class CoordinateSmoother:
    def __init__(self, alpha=0.35):
        self.alpha = max(0.05, min(0.95, float(alpha)))
        self.history = {}

    def smooth(self, track_id, center):
        x, y = float(center[0]), float(center[1])

        if track_id not in self.history:
            self.history[track_id] = (x, y)
            return [x, y]

        old_x, old_y = self.history[track_id]

        new_x = self.alpha * x + (1 - self.alpha) * old_x
        new_y = self.alpha * y + (1 - self.alpha) * old_y

        self.history[track_id] = (new_x, new_y)

        return [new_x, new_y]

    def remove(self, track_id):
        self.history.pop(track_id, None)

    def reset(self):
        self.history.clear()
