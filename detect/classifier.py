from collections import Counter
import json
import csv

from config import (
    CLASS_PLAYER, CLASS_RACKET, CLASS_BALL,
    SPEED_THRESHOLD, COOLDOWN_FRAMES, GROUND_FRACTION
)

#this one is to find center of bounding box, it will be useful for both racket and ball
# so i took edges and dvided by2 to get center
def bbox_center(box):
    
    x1, y1, x2, y2 = box.xyxy[0].tolist()
    return (x1 + x2) / 2, (y1 + y2) / 2


#the reason to create class instead of function was 
# to keep track of racket postion from previous
# if i did that in function i would have to pass that
# info every time and it would be messier, with class i can just store it as state

class ShotClassifier:
    def __init__(self):
        # this below will keep track of where the racket was in the last frame 
        # and how fast it was moving
        self.prev_rx  = None  # racket cx last frame
        self.prev_ry  = None  # racket cy last frame
        self.prev_spd = 0

        self.cooldown = 0  # wait a bit before detecting another shot
        self.shot_log = []  # store all the shots I find


    def _direction(self, rx, ry):
        # this one to find which way did the racket mostly move compared to last frame
        dx = rx - self.prev_rx
        dy = ry - self.prev_ry
        if abs(dy) > abs(dx) and dy < 0:
            return "up"
        return "right" if dx >= 0 else "left"

    def _shot_type(self, rx, ry, player_cx, head_y):
        # this one to figure out what kind of shot was made - forehand, backhand, or serve/smash
        # If the racket is above the head, it's a serve or smash. Otherwise, check which side
        if ry < head_y:
            return "serve_smash"
        if rx > player_cx:
            return "forehand"
        return "backhand"

    def update(self, result, frame_num, fps):
        # I check each frame to see if the racket is moving fast that means a shot is happening
        # First, I find where the player and racket are in this frame
        players, rackets = [], []
        for box in result.boxes:
            cls = int(box.cls[0])
            if cls == CLASS_PLAYER:
                players.append(box)
            elif cls == CLASS_RACKET:
                rackets.append(box)

        if not players or not rackets:
            self.prev_rx  = None
            self.prev_ry  = None
            self.prev_spd = 0
            return None

        player_box = players[0]
        racket_box = rackets[0]

        px, py  = bbox_center(player_box)
        rx, ry  = bbox_center(racket_box)
        head_y  = float(player_box.xyxy[0][1])
        pid     = int(player_box.id[0]) if player_box.id is not None else -1

        speed = 0.0
        if self.prev_rx is not None:
            # with that now calculate how far the racket moved since last frame
            dx    = rx - self.prev_rx
            dy    = ry - self.prev_ry
            speed = (dx**2 + dy**2) ** 0.5

        shot = None

        # bwlow one will detect a shot when the racket was going fast but now is going slower 
        peak_passed   = self.prev_spd > SPEED_THRESHOLD and speed < self.prev_spd
        not_on_cooldown = self.cooldown == 0

        if peak_passed and not_on_cooldown:
            shot_type = self._shot_type(rx, ry, px, head_y)
            direction = self._direction(rx, ry)
            ts        = round(frame_num / fps, 2)

            # I save this shot with all its information
            self.shot_log.append({
                "frame":      frame_num,
                "timestamp":  ts,
                "shot_type":  shot_type,
                "bounce":     False,
            })

            self.cooldown = COOLDOWN_FRAMES
            shot = shot_type
            print(f"[{frame_num}] {shot_type}")

        # Now we can update where the racket is now for the next frame
        self.prev_rx  = rx
        self.prev_ry  = ry
        self.prev_spd = speed
        if self.cooldown > 0:
            self.cooldown -= 1

        return shot

    def counts(self):
        # count how many shots of each type happened
        return Counter(s["shot_type"] for s in self.shot_log)

    def save_json(self, path):
        # save all the shots  found to a JSON file so we can look at them later
        with open(path, "w") as f:
            json.dump(self.shot_log, f, indent=2)
        print(f"saved {len(self.shot_log)} shots -> {path}")

    def save_csv(self, path):
        if not self.shot_log:
            return
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=self.shot_log[0].keys())
            w.writeheader()
            w.writerows(self.shot_log)
        print(f"saved {len(self.shot_log)} shots -> {path}")

    def print_summary(self):
        c = self.counts()
        print("\nshot summary")
        for k, v in sorted(c.items()):
            print(f"  {k}: {v}")
        print(f"  total: {len(self.shot_log)}")


# this one to detect ball bouncing everything same as above class
# record previous frames ball position and movement to find when it
#  bounces by looking for a change in direction near the ground
class BounceDetector:

    def __init__(self):
        self.prev_cy   = None  
        self.prev_dy   = 0  
        self.bounce_log = []  

    def update(self, result, frame_num, fps, frame_h):
        balls = [b for b in result.boxes if int(b.cls[0]) == CLASS_BALL]

        if not balls:
            self.prev_cy = None
            self.prev_dy = 0
            return False

        # bbox_center(balls[0]) will return cx horizontal center  and cy vertical center
        # and we need only vertical for bounce so take only cy
        cx, cy = bbox_center(balls[0])

        bounced = False
        if self.prev_cy is not None:
            dy          = cy - self.prev_cy
            near_ground = cy > frame_h * GROUND_FRACTION

            if self.prev_dy > 0 and dy < 0 and near_ground:
                ts = round(frame_num / fps, 2)
                self.bounce_log.append({"frame": frame_num, "timestamp": ts})
                print(f"[{frame_num}] bounce")
                bounced = True

            self.prev_dy = dy

        self.prev_cy = cy
        return bounced

    def mark_last_shot(self, shot_log):
        if shot_log:
            shot_log[-1]["bounce"] = True