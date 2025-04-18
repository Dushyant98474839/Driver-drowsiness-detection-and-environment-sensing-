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
# from dotenv import load_dotenv
import requests
import random

def sound_alarm(path):
    global alarm_status
    global alarm_status2
    global saying

    pygame.mixer.init()
    
    while alarm_status:
        print('Detected Drowsiness!!!')
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(1)
        except Exception as e:
            print(f"Error playing sound: {e}")
        time.sleep(1)

    if alarm_status2:
        print('Detected Drowsiness!!!')
        saying = True
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(1)
        except Exception as e:
            print(f"Error playing sound: {e}")
        saying = False
        time.sleep(1)

def encode_image(image_path):
    if os.path.exists(image_path):  
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    return None

LOG_FILE = "api_response_times.txt"

def log_api_response_time(response_time):
    """Logs the API response time to a file with a timestamp."""
    with open(LOG_FILE, "a") as f:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        f.write(f"{timestamp} - API Response Time: {response_time:.3f} sec\n")
    print(f"📄 Logged API response time: {response_time:.3f} sec")

def call_gemini_red_eye_detection(image_path):
    # load_dotenv()
    api_key = "yourapikeyhere"
    # api_key = os.getenv("API_KEY")
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
                # start_time = time.time()  # Start time before API call
                response = model.generate_content(input_content)
                # end_time = time.time()  # End time after API call
                
                # response_time = end_time - start_time
                # log_api_response_time(response_time)  # Log response time
                
                print("API Response:", response.text)
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


def capture_and_detect_red_eye():
    global tmp_pic
    while True:
        # print(tmp_pic)
        if (tmp_pic) is not None:
            filename = "red_eye_check.jpg"
            cv2.imwrite(filename, tmp_pic)
            print("📸 Image captured for red-eye detection")
            call_gemini_red_eye_detection(filename)
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

    
ap = argparse.ArgumentParser()
ap.add_argument("-w", "--webcam", type=int, default=0, help="index of webcam on system")
ap.add_argument("-a", "--alarm", type=str, default="Alert.WAV", help="path alarm .WAV file")
args = vars(ap.parse_args())

EYE_AR_THRESH = 0.3
EYE_AR_CONSEC_FRAMES = 30*5
YAWN_THRESH = 20
alarm_status = False
alarm_status2 = False
saying = False
COUNTER = 0

detector = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')

vs = VideoStream(src=args["webcam"]).start()
time.sleep(1.0)

red_flag=False
while True:
    frame = vs.read()
    tmp_pic=frame
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
        
        # Start red-eye detection thread
        if not red_flag:
            red_flag = True
            print("👁️ Starting red-eye detection thread")
            red_eye_thread = Thread(target=capture_and_detect_red_eye)
            red_eye_thread.daemon = True
            red_eye_thread.start()


        if ear < EYE_AR_THRESH:
            COUNTER += 1
            if COUNTER >= EYE_AR_CONSEC_FRAMES:
                if not alarm_status:
                    alarm_status = True
                    if args["alarm"]:
                        t = Thread(target=sound_alarm, args=(args["alarm"],))
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
                if args["alarm"]:
                    t = Thread(target=sound_alarm, args=(args["alarm"],))
                    t.daemon = True
                    t.start()
        else:
            alarm_status2 = False
        
        cv2.putText(frame, "EAR: {:.2f}".format(ear), (300, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(frame, "YAWN: {:.2f}".format(distance), (300, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break

cv2.destroyAllWindows()
vs.stop()
