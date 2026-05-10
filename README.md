## Methodology

### Getting the detections right

The first thing to solve was reliably detecting the player, racket, and ball in every frame. The initial approach was to combine separate open-source models one for the player, one for the racket, one for the ball. That didn't work well in practice. Running multiple models on every frame was slow, the detections weren't synced properly, and the overall output was choppy and unreliable.

The approach that actually worked was finding a single model on Roboflow that detected all three objects together, then retraining it on padel-specific footage for 200 epochs (about 2 hours of training). A single model is faster, more consistent, and the detections stay in sync because everything comes from one forward pass. The trained model also detected the net, but since that wasn't needed for shot classification it was just excluded by filtering class IDs in the tracking call.

### Classifying the shots

Once detections were stable, the shot classification was done using the geometry of the bounding boxes no separate classifier model needed.

The idea is straightforward: YOLO draws a box around the player and a box around the racket. From those boxes you can calculate the centre point of each. Every frame you also measure how fast the racket moved compared to the previous frame. When the racket speed peaks and then starts dropping, that moment is the swing. At that point you look at where the racket ended up relative to the player:

- Racket above the player's head → serve or smash
- Racket to the right of the player centre → forehand  
- Racket to the left → backhand

A cooldown window of ~15 frames after each shot prevents one swing from being logged multiple times during the follow-through.

Shot direction (left, right, up) and bounce detection were added on top using the same approach just watching how the racket and ball move between frames and applying simple rules.

### Output and visualisation

Every detected shot gets logged with its frame number, timestamp, shot type, direction, and player ID. At the end of the video this gets saved as both JSON and CSV. A bar chart PNG is also generated. While the video is running there's a live overlay showing the running shot counts in the corner of the frame.

---

## Challenges

**Getting a working detection model** was the biggest time sink. Separate models for each object sounded fine in theory but the results were bad laggy, inconsistent, and the detections from different models didn't play well together. Finding a combined model and retraining it took time but was the right call.

**Bounding box tracking IDs are unstable.** YOLO assigns a numeric ID to each tracked object and is supposed to keep that ID consistent across frames. In practice the same player might be ID 3 one second and ID 47 a moment later if the tracker loses them briefly. This makes "which player hit this shot" unreliable. It's logged as best-effort but it's a known limitation.

**Shot classification without pose data is inherently approximate.** The geometry approach works reasonably well but it's making assumptions mainly that the camera angle is roughly side-on and that the player is right-handed. A different camera angle or a left-handed player would break the forehand/backhand logic without adjustment. It also can't distinguish a forehand drive from a forehand volley, or a smash from a serve, since the racket position alone doesn't carry that information.

---

## Improvements

The most impactful improvement would be adding **pose estimation** (something like MediaPipe or a pose YOLO model) alongside the existing detections. With skeleton keypoints you'd know where the player's wrist, elbow, and shoulder actually are, which would make shot classification significantly more accurate and handle different camera angles properly. It would also let you distinguish things like a high backhand from a normal one.

**Player re-identification** would fix the unstable ID problem. Right now if the tracker loses a player for a few frames they come back with a new ID. A proper ReID model would match appearances across frames so the same person keeps the same label throughout the video.

For a production system you'd also want to **save an annotated output video** rather than just showing it on screen. Right now if you want to review the output you have to re-run the whole thing. Writing the annotated frames to a video file with `cv.VideoWriter` would be a small addition but makes the tool much more useful.

Finally the **forehand/backhand assumption** should be configurable. Right now the code assumes the player is right-handed and the camera is roughly side-on. Adding a config option to flip the forehand/backhand sides, and some basic camera angle correction, would make it work across more footage without code changes.

---

## Files

**`config.py`** — the only file you need to edit before running. Has your video path, model path, and the two numbers that control how sensitive shot detection is.

**`classifier.py`** — `ShotClassifier` (watches racket movement, fires shot events) and `BounceDetector` (watches ball vertical movement for bounces).

**`overlay.py`** — everything drawn on top of the video: the live shot count panel and the bar chart saved at the end.

**`main.py`** — the entry point. Opens the video, runs the loop, saves everything. About 50 lines.

---

## Setup

```
pip install -r requirements.txt
```

Put your video in `assets/` and the model in `models/`. Update paths in `config.py` if needed, then:

```
python main.py
```

Press `d` to stop early. Results save automatically when done.

Model weights and output videos: [[Google Drive link]](https://drive.google.com/drive/folders/18i6borVuBE51qJ384hF373iDeeTc_ndz?usp=drive_link)

---

## What gets saved

| File | What's in it |
|---|---|
| `shots.json` | Every shot — frame, timestamp, shot type, direction, player id, bounce flag |
| `shots.csv` | Same thing in spreadsheet format |
| `shot_chart.png` | Bar chart of forehand vs backhand vs serve/smash totals |

---

## Tuning

`SPEED_THRESHOLD = 8` in `config.py` — how fast the racket needs to be moving (pixels per frame) before we count it as a real swing. Raise if getting false positives, lower if missing shots.

`COOLDOWN_FRAMES = 15` — frames to ignore after a shot fires (~0.5s at 30fps). Raise if seeing duplicate shots from the same swing.
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
