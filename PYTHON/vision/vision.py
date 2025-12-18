import pyrealsense2 as rs
import numpy as np
import cv2

class RealSenseColorDetector:
    # 클래스 초기화
    def __init__(self, roi_area=(0, 0, 0, 0)):
        # ROI 검출 영역 설정
        self.y1, self.y2, self.x1, self.x2 = roi_area
        
        # RealSense 카메라와 프레임 스트림을 주고 받는 파이프라인 생성
        self.pipeline = rs.pipeline()
        # 파이프라인에 어떤 스트림을 사용할지 적어둘 설정서(config)
        config = rs.config()
        # 설정 : 컬러 스트림(해상도 640x480, 포맷 bgr8, 프레임레이트 30Hz)
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        # 설정 : 깊이 스트림(해상도 640x480, 포맷 z16(RAW depth값), 프레임레이트 30Hz)
        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        # 파이프라인을 설정한 config로 시작하겠다.
        profile = self.pipeline.start(config)
        # 현재 사용 중인 컬러 카메라의 내부 파라미터를 흭득
        self.intr = profile.get_stream(rs.stream.color).as_video_stream_profile().get_intrinsics()
        # z16과 곱해지는 스케일 값을 들고온다. (현재 코드에선 쓰이지 않음)
        self.depth_scale = profile.get_device().first_depth_sensor().get_depth_scale()
        # Depth 프레임을 Color 프레임의 좌표계에 맞춰 정렬하겠다.
        self.align = rs.align(rs.stream.color)
        
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
        # lower_green ≤ hsv_roi[y, x] ≤ upper_green
        # 범위 안에 있다면 255(흰색)
        # 범위 안에 없다면 0 (검정색)
        # 즉, ROI 영역 내에서, 초록색 부분만 흰색으로 보이고 나머지는 검정색으로 보인다.
        mask_green = cv2.inRange(hsv_roi, lower_green, upper_green)
        mask_blue = cv2.inRange(hsv_roi, lower_blue, upper_blue)
        mask_yellow = cv2.inRange(hsv_roi, lower_yellow, upper_yellow)
        
        # 딕셔너리 형태로 색깔의 면적을 계산한다.
        areas = {
            "RED": np.sum(mask_red > 0),
            "GREEN": np.sum(mask_green > 0),
            "BLUE": np.sum(mask_blue > 0),
            "YELLOW": np.sum(mask_yellow > 0)
        }
        
        # biggest = "RED" 이런식으로 면적이 가장 큰 색깔이 저장된다.
        biggest = max(areas, key=areas.get)
        
        # 실험적으로 설쟁해야된다.
        if areas[biggest] < 2200:
            return None, None
        
        if biggest == "RED":
            return "RED", mask_red
        elif biggest == "GREEN":
            return "GREEN", mask_green
        elif biggest == "BLUE":
            return "BLUE", mask_blue
        elif biggest == "YELLOW":
            return "YELLOW", mask_yellow
    
    def process_frame(self, color_image, depth_frame):
        # BGR8 포맷의 color_image를 HSV 색공간으로 변환
        # (480, 640, 3)
        # hsv_image[y, x] = [H, S, V]
        hsv_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2HSV)
        
        # color_image ROI 영역 슬라이싱
        roi = color_image[self.y1:self.y2, self.x1:self.x2]
        # hsv_image ROI 영역 슬라이싱
        hsv_roi = hsv_image[self.y1:self.y2, self.x1:self.x2]
        
        # 검출된 색깔, 마스크를 구한다.
        detected_color, selected_mask = self.detect_color(hsv_roi)
        
        # color_image와 동일한 크기, 동일한 자료형을 가지는 0(검정)으로 가득 찬 배열을 만든다.
        masked_view = np.zeros_like(color_image)
        # ROI 영역은 실제 color_image와 동일하게 채운다.
        masked_view[self.y1:self.y2, self.x1:self.x2] = color_image[self.y1:self.y2, self.x1:self.x2]
        # ROI 영역 하얀색 네모박스 생성 (실제 maksed_view 배열값을 바꾸면서 그리는거임)
        cv2.rectangle(masked_view, (self.x1, self.y1), (self.x2, self.y2), (255,255,255), 2)

        u = v = depth = None
        
        # 검출된 색깔이 있다면
        if detected_color:
            contours, _ = cv2.findContours(selected_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                if cv2.contourArea(cnt) < 500:
                    continue

                x, y, w_box, h_box = cv2.boundingRect(cnt)

                X = x + self.x1
                Y = y + self.y1
                
                cv2.rectangle(masked_view, (X, Y), (X + w_box, Y + h_box), (0, 255, 0), 2)
                
                cx = X + w_box // 2
                cy = Y + h_box // 2
                
                depth = depth_frame.get_distance(cx, cy) * 1000
                u, v = cx, cy

                cv2.drawMarker(masked_view, (cx, cy), (0, 255, 0), cv2.MARKER_CROSS, 20, 2)
                cv2.putText(masked_view, detected_color, (X, Y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
        
        # masked_view : 항상 존재하는 값
        # detected_color : None / 검출된 색
        # (u, v, depth) : None / 검출된 좌표
        return masked_view, detected_color, (u, v, depth)
    
    # 하나의 프레임만 탐지한다.
    def detect_one_frame(self):
        # 카메라에서 프레임 묶음이 들어올 때까지 기다렸다가 받아온다.
        frames = self.pipeline.wait_for_frames()
        # 받아온 프레임 묶음을 컬러 스트림 좌표계 기준으로 정렬해서 새 프레임 묶음을 만든다.
        # 즉, aligned = 정렬된 프레임 묶음
        aligned = self.align.process(frames)
        
        # 정렬된 프레임 묶음(aligned)에서 컬러 프레임, 깊이 프레임을 꺼낸다. 
        color_frame = aligned.get_color_frame()
        depth_frame = aligned.get_depth_frame()
        
        # 컬러프레임, 깊이 프레임중 하나라도 제대로 못받았다면
        if not color_frame or not depth_frame:
            # 모든 값 None으로 리턴
            return None, None, (None, None, None)
        
        # (height, width, channel)
        # (480, 640, 3)
        # color_image[100, 200] = [32, 120, 255]
        #                         [ B ,  G,  R ]
        color_image = np.asanyarray(color_frame.get_data())
        
        return self.process_frame(color_image, depth_frame)
    
    def stop(self):
        self.pipeline.stop()
        cv2.destroyAllWindows()