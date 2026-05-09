
## Working of code

- Detects and tracks the player, racket, and ball every frame
- Classifies each shot based on where the racket is relative to the player
- Detects when the ball bounces off the ground
- Shows a live overlay on the video with shot counts
- Saves results to `shots.json`, `shots.csv`, and a bar chart `shot_chart.png` when the video finishes

---

## Files

**`config.py`**
Has info on video to provide as input and place to store result and the two numbers that control how sensitive shot detection is. In case of false shot raising `SPEED_THRESHOLD` gets work done.


**`classifier.py`**
Two classes live here. `ShotClassifier` watches the racket every frame when it detects the racket just peaked in speed it calls that a shot and figures out which type based on where the racket ended up relative to the player.
`BounceDetector` watches the ball's vertical movement and flags a bounce when the ball switches from moving down to moving up near the bottom of the frame.

**`overlay.py`**
Handles everything visual that gets drawn on top of the video. The `CountPanel` class draws the semi-transparent shot count panel in the bottom corner and the big flashing label when a shot fires. `save_chart` draws a simple bar chart and saves it as a PNG when the video is done.

**`main.py`**
The entry point. Opens the video, runs the loop frame by frame, calls into the other files, and saves everything at the end. 
---

## How to run

1. Put your video in `assets/` and your model in `models/`
2. Update the paths in `config.py` if needed
3. Run:

```
python main.py
```

The stop key can be changed i have saved it as d and video gets saved upto taht point when quit
---

## What gets saved

`shots.json` Every shot with frame number, timestamp, shot type, direction, player id, whether a bounce followed
`shots.csv`  Same thing but in spreadsheet format
`shot_chart.png` Bar chart showing forehand vs backhand vs serve/smash totals 

---

## How shot detection actually works

The model gives us a bounding box around the player and the racket every frame. From those boxes we get the centre point of each. Every frame we also measure how fast the racket moved since last frame.

When the racket speed peaks and starts dropping — meaning the swing just happened — we look at where the racket centre is compared to the player centre:

- Racket above the player's head → serve or smash
- Racket to the right of the player → forehand
- Racket to the left → backhand

There's a cooldown of about 15 frames after each shot so one swing doesn't log ten times.

Shot direction (left/right/up) is logged separately by just checking which way the racket moved the most on that swing.

---

## Tuning

Everything worth tuning is in `config.py`. The two main ones:

`SPEED_THRESHOLD = 8`: how fast the racket needs to be moving before we consider it a real swing. Mihgt need raise this if random movement is triggering shots, lower this value if actual shots are being missed.

`COOLDOWN_FRAMES = 15`: how many frames to ignore after a shot fires. At 30fps that's about half a second. Raise it if there is duplicate shots from the same swing.

## Sample outputs
`
[
  {
    "frame": 14,
    "timestamp": 0.56,
    "shot_type": "forehand",
    "bounce": false
  },
  {
    "frame": 140,
    "timestamp": 5.6,
    "shot_type": "backhand",
    "bounce": false
  },
  {
    "frame": 156,
    "timestamp": 6.24,
    "shot_type": "backhand",
    "bounce": false
  }]
`
### Chart image
<img width="631" height="481" alt="image" src="https://github.com/user-attachments/assets/26c505c6-b78f-43a4-9529-cadeceb65982" />

### Tracking process
<img width="1919" height="960" alt="image" src="https://github.com/user-attachments/assets/7b98cdd1-ff3a-4a2d-b2b5-f1756b4ffb96" />

<img width="1919" height="1028" alt="image" src="https://github.com/user-attachments/assets/8c3aa5c3-38da-4416-885f-01b82e6cd68a" />
