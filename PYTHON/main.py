# from modbus.client import ModbusTCPClient
# from modbus.server import ModbusTCPServer
# from robot.robot import dobot
# from uart.uart import uart
# from vision.vision import vision
import pyrealsense2 as rs
import numpy as np
import cv2

def detect_color(hsv_roi):
    lower_red1 = np.array([0, 120, 70])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 120, 70])
    upper_red2 = np.array([180, 255, 255])

    lower_green = np.array([35, 80, 80])
    upper_green = np.array([85, 255, 255])

    lower_blue = np.array([90, 80, 80])
    upper_blue = np.array([130, 255, 255])

    lower_yellow = np.array([20, 100, 100])
    upper_yellow = np.array([35, 255, 255])
    
    mask_red = cv2.bitwise_or(
        cv2.inRange(hsv_roi, lower_red1, upper_red1),
        cv2.inRange(hsv_roi, lower_red2, upper_red2)
    )
    mask_green = cv2.inRange(hsv_roi, lower_green, upper_green)
    mask_blue = cv2.inRange(hsv_roi, lower_blue, upper_blue)
    mask_yellow = cv2.inRange(hsv_roi, lower_yellow, upper_yellow)

    areas = {
        "RED": np.sum(mask_red > 0),
        "GREEN": np.sum(mask_green > 0),
        "BLUE": np.sum(mask_blue > 0),
        "YELLOW": np.sum(mask_yellow > 0)
    }
    
    biggest = max(areas, key=areas.get)
    
    if areas[biggest] < 300:
        return None, None
    
    if biggest == "RED":
        return "RED", mask_red
    elif biggest == "GREEN":
        return "GREEN", mask_green
    elif biggest == "BLUE":
        return "BLUE", mask_blue
    elif biggest == "YELLOW":
        return "YELLOW", mask_yellow


# ---------------------------------------------------------
# 웹캠 입력
# ---------------------------------------------------------
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("웹캠을 열 수 없습니다.")
    exit()

try:
    while True:
        ret, color_image = cap.read()
        if not ret:
            continue

        hsv_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2HSV)

        h, w, _ = color_image.shape
        
        # ROI 설정 (임의로 아래 150px, 양옆 100px 제외)
        y1, y2 = h - 320, h - 220
        x1, x2 = 380, w - 100

        roi = color_image[y1:y2, x1:x2]
        hsv_roi = hsv_image[y1:y2, x1:x2]

        detected_color, selected_mask = detect_color(hsv_roi)

        masked_view = np.zeros_like(color_image)
        masked_view[y1:y2, x1:x2] = color_image[y1:y2, x1:x2]
        cv2.rectangle(masked_view, (x1, y1), (x2, y2), (255,255,255), 2)

        if detected_color:
            contours, _ = cv2.findContours(selected_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                if cv2.contourArea(cnt) < 300:
                    continue

                x, y, w_box, h_box = cv2.boundingRect(cnt)

                X = x + x1
                Y = y + y1

                cv2.rectangle(masked_view, (X, Y), (X + w_box, Y + h_box), (0, 255, 0), 2)

                cx = X + w_box // 2
                cy = Y + h_box // 2

                cv2.drawMarker(masked_view, (cx, cy), (0, 255, 0), cv2.MARKER_CROSS, 20, 2)
                cv2.putText(masked_view, detected_color, (X, Y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

            print("[COLOR DETECTED]", detected_color)

        cv2.imshow("WEB CAM ROI MASK", masked_view)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
