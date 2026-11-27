import cv2
import time
import requests
import json

# 1. Initialize the default webcam (use 1 or 2 for external cameras)
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))

detector = cv2.QRCodeDetector()
BACKEND_URL = "http://localhost:8000/"

if not cap.isOpened():
    print("Error: Could not access the camera.")
    exit()

def send_pickup(order_id: str, student_id: str):
    url = f"{BACKEND_URL}/orders/{order_id}/pickup"
    try:
        res = requests.post(url, json={"student_id": student_id}, timeout=5)
        
        if res.ok:
            print("Success:", res.json())
        else:
            print(f"Rejected ({res.status_code}):", res.json().get("detail", res.text))  
    except requests.RequestException as exc:
        print("Could not reach backend:", exc)

# 2. Continuously capture and display frames
while True:
    ret, frame = cap.read()
    
    # Break the loop if a frame is not successfully captured
    if not ret:
        print("Error: Failed to grab frame.")
        break

    # Display the resulting frame in a window
    cv2.imshow("Camera Feed", frame)

    data, _, _ = detector.detectAndDecode(frame)

    if data:
        try:
            payload = json.loads(data)
            order_id = payload["order_id"]
            student_id = payload["student_id"]
            
            send_pickup(order_id, student_id)
        except (json.JSONDecodeError, KeyError, TypeError):
            print("Invalid QR payload:", data)

        time.sleep(2)

    # 3. Wait 1ms for a key press; exit if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 4. Release the camera hardware and close all OpenCV windows
cap.release()
cv2.destroyAllWindows()