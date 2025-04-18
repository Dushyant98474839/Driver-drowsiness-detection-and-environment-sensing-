# final.py
from picamera2 import Picamera2
from scipy.spatial import distance as dist
from imutils.video import VideoStream
from imutils import face_utils
from threading import Thread
import numpy as np
import argparse
import imutils
import time
import dlib
import cv2
import os
import pygame
import base64
import google.generativeai as genai
import queue
import random

# Initialize the camera
picam2 = Picamera2()
picam2.preview_configuration.main.size = (1280, 720)
picam2.preview_configuration.main.format = "BGR888"
picam2.preview_configuration.align()
picam2.configure("preview")
picam2.start()
time.sleep(2)

def sound_alarm(path, alert_queue):
    global alarm_status, alarm_status2, saying
    pygame.mixer.init()
    while alarm_status or alarm_status2:
        if alarm_status:
            print("Detected Drowsiness, sending alert...")
            alert_queue.put(f"Drowsiness detected at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        if alarm_status2:
            print("Detected Yawn, sending alert...")
            alert_queue.put(f"Yawn detected at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(1)
        except Exception as e:
            print(f"Error playing sound: {e}")
        time.sleep(1)

def encode_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    return None

LOG_FILE = "api_response_times.txt"

def log_api_response_time(response_time):
    with open(LOG_FILE, "a") as f:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        f.write(f"{timestamp} - API Response Time: {response_time:.3f} sec\n")
    print(f"📄 Logged API response time: {response_time:.3f} sec")

def call_gemini_red_eye_detection(image_path, alert_queue):
    api_key = ""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")

    encoded_image = encode_image(image_path)
    if not encoded_image:
        print(f"Error encoding image: {image_path}")
        return

    input_content = [
        {"text": "Detect any red-eye symptoms in this image. Respond with only 'yes' or 'no', strictly nothing else."},
        {"mime_type": "image/jpg", "data": encoded_image}
    ]

    def safe_api_call(input_content, max_retries=5):
        retries = 0
        while retries < max_retries:
            try:
                response = model.generate_content(input_content)
                print("API Response:", response.text)
                if response.text.strip().lower() == 'yes':
                    print("Red-eye detected, sending alert...")
                    alert_queue.put(f"Red-eye detected at {time.strftime('%Y-%m-%d %H:%M:%S')}")
                return response
            except Exception as e:
                print(f"API Error: {e}")
                wait_time = (2 ** retries) + random.uniform(0, 1)
                print(f"Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
                retries += 1
        print("Max retries reached. Skipping.")
        return None

    response = safe_api_call(input_content)
    if response:
        print("Response:", response.text)

def capture_and_detect_red_eye(alert_queue):
    global tmp_pic
    while True:
        if tmp_pic is not None:
            filename = "red_eye_check.jpg"
            cv2.imwrite(filename, tmp_pic)
            print("📸 Image captured for red-eye detection")
            call_gemini_red_eye_detection(filename, alert_queue)
        time.sleep(5)

def eye_aspect_ratio(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

def final_ear(shape):
    (lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
    (rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]
    leftEye = shape[lStart:lEnd]
    rightEye = shape[rStart:rEnd]
    leftEAR = eye_aspect_ratio(leftEye)
    rightEAR = eye_aspect_ratio(rightEye)
    ear = (leftEAR + rightEAR) / 2.0
    return (ear, leftEye, rightEye)

def lip_distance(shape):
    top_lip = shape[50:53]
    top_lip = np.concatenate((top_lip, shape[61:64]))
    low_lip = shape[56:59]
    low_lip = np.concatenate((low_lip, shape[65:68]))
    top_mean = np.mean(top_lip, axis=0)
    low_mean = np.mean(low_lip, axis=0)
    distance = abs(top_mean[1] - low_mean[1])
    return distance

def run_drowsiness_detection(alert_queue, alarm_path="Alert.wav"):
    print("Drowsiness detection started")
    global alarm_status, alarm_status2, saying, tmp_pic
    EYE_AR_THRESH = 0.30
    EYE_AR_CONSEC_FRAMES = 30*3 
    YAWN_THRESH = 20
    alarm_status = False
    alarm_status2 = False
    saying = False
    COUNTER = 0

    detector = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
    predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')

    red_flag = False
    while True:
        frame = picam2.capture_array()
        tmp_pic = frame
        frame = imutils.resize(frame, width=450)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rects = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30), flags=cv2.CASCADE_SCALE_IMAGE)

        for (x, y, w, h) in rects:
            rect = dlib.rectangle(int(x), int(y), int(x + w), int(y + h))
            shape = predictor(gray, rect)
            shape = face_utils.shape_to_np(shape)
            eye = final_ear(shape)
            ear = eye[0]
            leftEye = eye[1]
            rightEye = eye[2]
            distance = lip_distance(shape)
            leftEyeHull = cv2.convexHull(leftEye)
            rightEyeHull = cv2.convexHull(rightEye)
            cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
            cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)
            lip = shape[48:60]
            cv2.drawContours(frame, [lip], -1, (0, 255, 0), 1)

            if not red_flag:
                red_flag = True
                print("👁️ Starting red-eye detection thread")
                red_eye_thread = Thread(target=capture_and_detect_red_eye, args=(alert_queue,))
                red_eye_thread.daemon = True
                red_eye_thread.start()

            if ear < EYE_AR_THRESH:
                COUNTER += 1
                if COUNTER >= EYE_AR_CONSEC_FRAMES:
                    if not alarm_status:
                        alarm_status = True
                        if alarm_path:
                            t = Thread(target=sound_alarm, args=(alarm_path, alert_queue))
                            t.daemon = True
                            t.start()
                    cv2.putText(frame, "DROWSINESS ALERT!", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                COUNTER = 0
                alarm_status = False

            if distance > YAWN_THRESH:
                cv2.putText(frame, "Yawn Alert", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                if not alarm_status2 and not saying:
                    alarm_status2 = True
                    if alarm_path:
                        t = Thread(target=sound_alarm, args=(alarm_path, alert_queue))
                        t.daemon = True
                        t.start()
            else:
                alarm_status2 = False

            cv2.putText(frame, "EAR: {:.2f}".format(ear), (300, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(frame, "YAWN: {:.2f}".format(distance), (300, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        time.sleep(0.1)

if __name__ == "__main__":
    try:
        run_drowsiness_detection(queue.Queue())  # For standalone testing
    except KeyboardInterrupt:
        print("Drowsiness detection terminated")
        picam2.stop()
        cv2.destroyAllWindows()
