# import torch
# from ultralytics.nn.tasks import DetectionModel
# from torch.nn import Sequential
# from ultralytics.nn.modules import Conv  # Add this import

# torch.serialization.add_safe_globals([DetectionModel, Sequential, Conv])  # Add Conv here


import numpy as np
from flask import Flask, jsonify, render_template, request, Response
import cv2
import cvzone
import math
from sort import *
from ultralytics import YOLO
import threading
import os

app = Flask(__name__)

# Load YOLOv8 model
model = YOLO('../Yolo-Weights/yolov8n.pt')
classNames = ["person", "bicycle", "car", "motorbike", "aeroplane", "bus", "train", "truck", "boat",
              "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
              "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella",
              "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite", "baseball bat",
              "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
              "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange", "broccoli",
              "carrot", "hot dog", "pizza", "donut", "cake", "chair", "sofa", "pottedplant", "bed",
              "diningtable", "toilet", "tvmonitor", "laptop", "mouse", "remote", "keyboard", "cell phone",
              "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors",
              "teddy bear", "hair drier", "toothbrush"]

lane_counts = {'lane1': 0, 'lane2': 0, 'lane3': 0, 'lane4': 0}
tracker = Sort(max_age=20, min_hits=3, iou_threshold=0.3)

limits = {
    'lane1': (400, 297, 673, 297),
    'lane2': (400, 297, 673, 297),
    'lane3': (400, 297, 673, 297),
    'lane4': (400, 297, 673, 297)
}


# first 
def generate_frames(lane, video_path, mask_path):
    cap = cv2.VideoCapture(video_path)
    mask = cv2.imread(mask_path)
    totalCount = []

    while True:
        success, img = cap.read()
        if not success:
            break

        imgRegion = cv2.bitwise_and(img, mask)
        results = model(imgRegion, stream=True)
        detections = np.empty((0, 5))

        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                w, h = x2 - x1, y2 - y1
                conf = math.ceil(box.conf[0] * 100) / 100
                cls = int(box.cls[0])
                currentClass = classNames[cls]

                if currentClass in ["car", "truck", "bus", "motorbike"] and conf > 0.3:
                    currentArray = np.array([x1, y1, x2, y2, conf])
                    detections = np.vstack((detections, currentArray))

        resultstracker = tracker.update(detections)
        limit = limits[lane]
        cv2.line(img, (limit[0], limit[1]), (limit[2], limit[3]), (0, 0, 255), 5)

        for result in resultstracker:
            x1, y1, x2, y2, id = result
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            w, h = x2 - x1, y2 - y1
            cx, cy = x1 + w // 2, y1 + h // 2

            if limit[0] < cx < limit[2] and limit[1] - 20 < cy < limit[1] + 20:
                if totalCount.count(id) == 0:
                    totalCount.append(id)

        lane_counts[lane] = len(totalCount)
        cvzone.putTextRect(img, f'Lane {lane[-1]} Count: {lane_counts[lane]}', (50, 50))

        # Show video in local OpenCV window
        # cv2.imshow(f"Lane {lane[-1]} - Local View", img)
        # if cv2.waitKey(1) & 0xFF == ord('q'):
            # break

        # Stream video to web browser
        ret, buffer = cv2.imencode('.jpg', img)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()
    cv2.destroyAllWindows()



@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_count')
def get_count():
    return jsonify(lane_counts)

@app.route('/video_feed/<lane>')

def video_feed(lane):
    video_path = f"../Videos/{lane}.mp4"
    mask_path = f"mask{int(lane[-1])}.png"
    return Response(generate_frames(lane, video_path, mask_path),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True)


