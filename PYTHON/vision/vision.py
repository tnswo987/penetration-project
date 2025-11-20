import pyrealsense2 as rs
import numpy as np
import cv2

class RealSenseColorDetector:
    def __init__(self, roi_area=(0, 0, 0, 0)):
        self.y1, self.y2, self.x1, self.x2 = roi_area
        
        self.pipeline = rs.pipeline()
        config = rs.config()
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        self.pipeline.start(config)
    
    def detect_color(self, hsv_roi):
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
        # green 색 범위에 속하는 픽셀은 255 / 아니면 0으로 처리 (2진 처리)
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
        
        # 경험적으로 판단해봐야할 거 같다.
        if areas[biggest] < 1500:
            return None, None
        
        if biggest == "RED":
            return "RED", mask_red
        elif biggest == "GREEN":
            return "GREEN", mask_green
        elif biggest == "BLUE":
            return "BLUE", mask_blue
        elif biggest == "YELLOW":
            return "YELLOW", mask_yellow
    
    def process_frame(self, color_image):
        hsv_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2HSV)
        
        roi = color_image[self.y1:self.y2, self.x1:self.x2]
        hsv_roi = hsv_image[self.y1:self.y2, self.x1:self.x2]
        
        # 검출된 색깔, 마스크를 구한다.
        detected_color, selected_mask = self.detect_color(hsv_roi)
        
        # color_image와 동일한 크기, 동일한 자료형을 가지는 0으로 가득 찬 배열을 만든다.
        masked_view = np.zeros_like(color_image)
        # ROI 영역은 실제 color_image와 동일하게 채운다.
        masked_view[self.y1:self.y2, self.x1:self.x2] = color_image[self.y1:self.y2, self.x1:self.x2]
        # ROI 영역 하얀색 네모박스 생성
        cv2.rectangle(masked_view, (self.x1, self.y1), (self.x2, self.y2), (255,255,255), 2)

        if detected_color:
            contours, _ = cv2.findContours(selected_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                if cv2.contourArea(cnt) < 300:
                    continue

                x, y, w_box, h_box = cv2.boundingRect(cnt)

                X = x + self.x1
                Y = y + self.y1

                cv2.rectangle(masked_view, (X, Y), (X + w_box, Y + h_box), (0, 255, 0), 2)
                cx = X + w_box // 2
                cy = Y + h_box // 2

                cv2.drawMarker(masked_view, (cx, cy), (0, 255, 0), cv2.MARKER_CROSS, 20, 2)
                cv2.putText(masked_view, detected_color, (X, Y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
        
        return masked_view, detected_color
    
    def detect_one_frame(self):
        frames = self.pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        
        if not color_frame:
            return None, None
        
        color_image = np.asanyarray(color_frame.get_data())
        view, detected_color = self.process_frame(color_image)
        
        return view, detected_color
    
    def stop(self):
        self.pipeline.stop()
        cv2.destroyAllWindows()