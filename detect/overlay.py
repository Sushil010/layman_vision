import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt

from config import LABEL_DURATION

SHOT_COLORS = {
    "forehand":    (0,   165, 255),
    "backhand":    (180, 105, 255),
    "serve_smash": (0,   200,  80),
}


class CountPanel:

    def __init__(self):
        self.timer     = 0
        self.last_shot = None

    def notify(self, shot_type):
        self.last_shot = shot_type
        self.timer     = LABEL_DURATION

    def draw(self, frame, counts, bounce_count):
        h, w = frame.shape[:2]

        # big flashing label top-left when a shot just happened
        if self.timer > 0 and self.last_shot:
            color = SHOT_COLORS.get(self.last_shot, (255, 255, 255))
            cv.putText(frame, self.last_shot.upper(), (20, 52),
                       cv.FONT_HERSHEY_SIMPLEX, 1.3, color, 3, cv.LINE_AA)
            self.timer -= 1

        # analytics panel at bottom left corner
        px, py = 14, h - 140
        pw, ph = 210, 120

        # semi transparent background for the panel (used AI for this portion to make visibly better)
        panel = frame.copy()
        cv.rectangle(panel, (px, py), (px + pw, py + ph), (20, 20, 20), -1)
        cv.addWeighted(panel, 0.6, frame, 0.4, 0, frame)

        cv.putText(frame, "shot analytics", (px + 8, py + 18),
                   cv.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1, cv.LINE_AA)

        shot_types = ["forehand", "backhand", "serve_smash"]
        max_count  = max((counts.get(s, 0) for s in shot_types), default=1) or 1

        for i, shot in enumerate(shot_types):
            y      = py + 36 + i * 26
            count  = counts.get(shot, 0)
            color  = SHOT_COLORS[shot]
            bar_w  = int(80 * count / max_count) if count else 2

            cv.rectangle(frame, (px + 8, y - 10), (px + 8 + bar_w, y + 4), color, -1)
            cv.putText(frame, f"{shot:<12} {count}", (px + 96, y + 2),
                       cv.FONT_HERSHEY_SIMPLEX, 0.42, (220, 220, 220), 1, cv.LINE_AA)

        bounce_y = py + 36 + len(shot_types) * 26 - 10
        cv.putText(frame, f"bounces         {bounce_count}", (px + 8, bounce_y),
                   cv.FONT_HERSHEY_SIMPLEX, 0.42, (160, 160, 160), 1, cv.LINE_AA)


def save_chart(counts, path):
    if not counts:
        print("no shots to chart")
        return

    shots = ["forehand", "backhand", "serve_smash"]
    values = [counts.get(shot, 0) for shot in shots]
    
    plt.figure()
    plt.bar(shots, values)
    plt.savefig(path)
    plt.close()
    
    print(f"chart saved -> {path}")