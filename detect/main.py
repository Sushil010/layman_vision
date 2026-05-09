from ultralytics import YOLO
import cv2 as cv

from config import (
    VIDEO_PATH, MODEL_PATH, TRACK_CLASSES,
    JSON_OUT, CSV_OUT, CHART_OUT, VIDEO_OUT
)
from classifier import ShotClassifier, BounceDetector
from overlay import CountPanel, save_chart


model = YOLO(MODEL_PATH)
print("classes:", model.names)

vid     = cv.VideoCapture(VIDEO_PATH)
fps     = vid.get(cv.CAP_PROP_FPS) or 30.0
frame_h = int(vid.get(cv.CAP_PROP_FRAME_HEIGHT) * 0.50)
frame_w = int(vid.get(cv.CAP_PROP_FRAME_WIDTH) * 0.50)

# I'll set up a video writer to save the tracked video
fourcc = cv.VideoWriter_fourcc(*'mp4v')
out    = cv.VideoWriter(VIDEO_OUT, fourcc, fps, (frame_w, frame_h))

classifier = ShotClassifier()
bouncer    = BounceDetector()
hud        = CountPanel()

frame_num = 0

while True:
    ok, frame = vid.read()
    if not ok:
        break

    frame_num += 1

    # resize to 50% - faster inference
    h, w  = frame.shape[:2]
    small = cv.resize(frame, (w // 2, h // 2), interpolation=cv.INTER_AREA)

    results = model.track(small, persist=True, conf=0.25, classes=TRACK_CLASSES)
    r       = results[0]

    shot = classifier.update(r, frame_num, fps)
    if shot:
        hud.notify(shot)

    bounced = bouncer.update(r, frame_num, fps, frame_h)
    if bounced:
        bouncer.mark_last_shot(classifier.shot_log)

    frame_out = r.plot(conf=False)
    hud.draw(frame_out, classifier.counts(), len(bouncer.bounce_log))

    # I save the processed frame to the output video
    out.write(frame_out)

    cv.imshow("tennis analyser", frame_out)
    if cv.waitKey(1) & 0xFF == ord('d'):
        break

vid.release()
out.release()
cv.destroyAllWindows()

# save everything
classifier.save_json(JSON_OUT)
classifier.save_csv(CSV_OUT)
classifier.print_summary()
save_chart(classifier.counts(), CHART_OUT)