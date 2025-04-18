import threading
import queue
import time
import os
import pygame
import firebase_admin
from firebase_admin import credentials, messaging
from working import run_sensor_loop
from final2 import run_drowsiness_detection

# Initialize Firebase by creating your certificate and replace here
cred = credentials.Certificate("hcai-project-cdaf1-firebase-adminsdk-fbsvc-309022b7c8.json")
firebase_admin.initialize_app(cred)

# Shared alert queue
alert_queue = queue.Queue()

# Log file for alerts
ALERT_LOG_FILE = "alerts_log.txt"

def log_alert(message):
    """Log alerts to a file."""
    with open(ALERT_LOG_FILE, "a") as f:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        f.write(f"{timestamp} - {message}\n")
    print(f"📄 Logged alert: {message}")

def send_fcm_notification(message):
    """Send push notification to mobile app via Firebase."""
    try:
        # Use the FCM registration token from the Android app
        FCM_TOKEN = ""  # Replace with the token from Step 1
        notification = messaging.Message(
            notification=messaging.Notification(
                title="Drowsiness Detection Alert",
                body=message,
            ),
            token=FCM_TOKEN,  # Send to specific device
            # Alternatively, use topic="alerts" to broadcast to all subscribed devices
        )
        response = messaging.send(notification)
        print(f"Sent FCM notification: {response}")
    except Exception as e:
        print(f"Error sending FCM notification: {e}")

def alert_handler():
    """Handle alerts from the queue, log them, play sound, and send to FCM."""
    pygame.mixer.init()
    sound_file = "Alert.wav"
    
    while True:
        try:
            message = alert_queue.get(timeout=1)
            print(f"🚨 Processing alert: {message}")
            log_alert(message)
            send_fcm_notification(message)
            
            # Play alert sound
            try:
                pygame.mixer.music.load(sound_file)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(1)
            except Exception as e:
                print(f"Error playing sound: {e}")
                
            alert_queue.task_done()
        except queue.Empty:
            continue
        except Exception as e:
            print(f"Error in alert handler: {e}")

def main():
    print("Starting main application...")
    
    # Start alert handler thread
    alert_thread = threading.Thread(target=alert_handler, daemon=True)
    alert_thread.start()
    print("Started alert handler thread")
    
    # Start sensor thread
    sensor_thread = threading.Thread(target=run_sensor_loop, args=(alert_queue,), daemon=True)
    sensor_thread.start()
    print("Started sensor thread")
    
    # Start drowsiness detection thread
    drowsiness_thread = threading.Thread(target=run_drowsiness_detection, args=(alert_queue,), daemon=True)
    drowsiness_thread.start()
    print("Started drowsiness detection thread")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        # Cleanup if needed
        pygame.mixer.quit()

if __name__ == "__main__":
    main()
