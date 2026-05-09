VIDEO_PATH  = "assets/infernce_sample_video.mp4"
MODEL_PATH  = "models/all_best.pt"

# these classes are from the trained model can be seen by printing
# print(model.names)
CLASS_PLAYER = 0
CLASS_BALL   = 2
CLASS_RACKET = 3
TRACK_CLASSES = [CLASS_PLAYER, CLASS_BALL, CLASS_RACKET]

# these thresholds are for device compatability as mine was slow so
#  I had to lower the speed threshold and increase cooldown frames 

SPEED_THRESHOLD = 8    # in simple it is how fast racket move
COOLDOWN_FRAMES = 15   # after a shot is detected, how many frames to ignore before looking for the next one

# in simple term if ball is in bottom 30% of frame from human we consider it bounced
GROUND_FRACTION = 0.70

# this is just to make text appear in screen for few frmes
LABEL_DURATION = 40


# output file names, it cpuld have been in main but i thought config is better for it
JSON_OUT  = "shots.json"
CSV_OUT   = "shots.csv"
CHART_OUT = "shot_chart.png"
VIDEO_OUT = "tracked_video.mp4"