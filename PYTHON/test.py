from vision.vision import RealSenseColorDetector
from uart.uart import uart
import cv2

detector = RealSenseColorDetector(roi_area=(230, 280, 425, 475))
comm = uart('COM4', 9600)

try:
    while True:
        view, color = detector.detect_one_frame()
        if view is not None:
            cv2.imshow("Color Detection", view)
            if color:
                data = "001"
                comm.send(data)
                print("Detected color:", color)
        
        # 'q' 키를 누르면 종료
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    detector.stop()