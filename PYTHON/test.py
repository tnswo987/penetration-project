import pyrealsense2 as rs
import numpy as np
import cv2

pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

profile = pipeline.start(config)

depth_sensor = profile.get_device().first_depth_sensor()
depth_scale = depth_sensor.get_depth_scale()

align_to = rs.stream.color
align = rs.align(align_to)

lower_red1 = np.array([0, 120, 70])
upper_red1 = np.array([10, 255, 255])
lower_red2 = np.array([170, 120, 70])
upper_red2 = np.array([180, 255, 255])

try:
    while True:
        frames = pipeline.wait_for_frames()
        aligned_frames = align.process(frames)
        color_frame = aligned_frames.get_color_frame()
        depth_frame = aligned_frames.get_depth_frame()

        if not color_frame:
            continue
        if not depth_frame:
            continue

        color_image = np.asanyarray(color_frame.get_data())
        depth_image = np.asanyarray(depth_frame.get_data())

        hsv_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2HSV)

        mask1 = cv2.inRange(hsv_image, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv_image, lower_red2, upper_red2)
        mask_sum = cv2.bitwise_or(mask1, mask2)
        final_mask = cv2.bitwise_and(color_image, color_image, mask=mask_sum)

        contours, _ = cv2.findContours(mask_sum, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for i in contours:
            area = cv2.contourArea(i)
            if area > 1000:
                x, y, w, h = cv2.boundingRect(i)
                cv2.rectangle(color_image, (x, y), (x + w, y + h), (0, 255, 0), 2)

                cx = x + w // 2
                cy = y + h // 2

                depth = depth_frame.get_distance(cx, cy)
                depth_data = f"({cx}px, {cy}px, {depth * 1000:.2f}mm)"

                cv2.drawMarker(
                    color_image, (cx, cy), (255, 255, 0),
                    markerType=cv2.MARKER_CROSS, markerSize=20, thickness=2
                )
                cv2.putText(color_image, depth_data, (cx - 60, cy - 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                cv2.putText(color_image, f"Pixel Area : {int(area)}",
                            (cx - 50, cy - 120),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        cv2.putText(color_image, "SSAFY_14th Vision", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (250, 250, 250), 2)

        cv2.imshow("Color Image", color_image)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    pipeline.stop()
    cv2.destroyAllWindows()
