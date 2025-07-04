import cv2
import threading
from ultralytics import YOLO
import time

# Thay mã xác thực (LCGSXD) và IP (192.168.1.177)
rtsp_url = "rtsp://admin:LCGSXD@192.168.1.177:554/h264/ch1/sub/av_stream"

# Tải mô hình YOLOv8 đã được huấn luyện sẵn
model = YOLO("yolov8n.pt")  # sử dụng mô hình nhỏ nhất để tốc độ cao nhất

# Thiết lập tham số cho camera để giảm độ trễ
cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Giảm buffer size xuống 1 frame
cap.set(cv2.CAP_PROP_FPS, 30)  # Đặt FPS cao

if not cap.isOpened():
    print("❌ Không thể kết nối camera! Kiểm tra lại IP/RTSP URL.")
    exit()

# Các class của COCO dataset mà YOLOv8 được huấn luyện
# Class ID 0 là người (person)
person_class_id = 0

# Biến toàn cục để chia sẻ dữ liệu giữa các luồng
latest_frame = None
processing_frame = None
detection_results = []
frame_ready = threading.Event()
results_ready = threading.Event()
stop_threads = False

# Đo FPS
frame_count = 0
detection_count = 0
last_fps_time = time.time()
fps_interval = 2.0  # Hiển thị FPS mỗi 2 giây
fps_display = 0
detection_fps_display = 0

# Luồng riêng để đọc frame từ camera
def capture_thread():
    global latest_frame, frame_ready, stop_threads, frame_count
    
    while not stop_threads:
        ret, frame = cap.read()
        if ret:
            latest_frame = frame.copy()
            frame_ready.set()
            frame_count += 1
        else:
            time.sleep(0.001)  # Tránh sử dụng quá nhiều CPU khi không đọc được frame

# Luồng riêng để xử lý YOLO
def detection_thread():
    global latest_frame, processing_frame, detection_results, frame_ready, results_ready, stop_threads, detection_count
    
    while not stop_threads:
        frame_ready.wait(timeout=1.0)
        if frame_ready.is_set():
            frame_ready.clear()
            if latest_frame is not None:
                processing_frame = latest_frame.copy()
                # Chạy YOLO với cài đặt tối ưu tốc độ
                results = model.predict(processing_frame, conf=0.5, verbose=False, stream=True)
                detection_results = next(results)
                detection_count += 1
                results_ready.set()

# Bắt đầu các luồng
capture_thread = threading.Thread(target=capture_thread)
detection_thread = threading.Thread(target=detection_thread)
capture_thread.daemon = True
detection_thread.daemon = True
capture_thread.start()
detection_thread.start()

try:
    while True:
        if results_ready.is_set():
            results_ready.clear()
            
            # Xử lý kết quả
            detected_persons = 0
            result = detection_results
            
            # Tạo bản sao của frame để vẽ lên
            display_frame = processing_frame.copy()
            
            if result.boxes is not None:
                boxes = result.boxes
                for box in boxes:
                    # Kiểm tra xem đối tượng có phải là người không
                    if int(box.cls[0]) == person_class_id:
                        detected_persons += 1
                        
                        # Lấy tọa độ bounding box
                        x1, y1, x2, y2 = box.xyxy[0]
                        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                        
                        # Vẽ bounding box
                        cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        
                        # Hiển thị nhãn và độ tin cậy
                        conf = float(box.conf[0])
                        label = f"Person: {conf:.2f}"
                        cv2.putText(display_frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Tính và hiển thị FPS
            current_time = time.time()
            if current_time - last_fps_time >= fps_interval:
                fps_display = frame_count / (current_time - last_fps_time)
                detection_fps_display = detection_count / (current_time - last_fps_time)
                frame_count = 0
                detection_count = 0
                last_fps_time = current_time
            
            # Hiển thị thông tin
            cv2.putText(display_frame, f"Persons: {detected_persons}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(display_frame, f"Camera FPS: {fps_display:.1f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(display_frame, f"Detection FPS: {detection_fps_display:.1f}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Hiển thị frame
            cv2.imshow("EZVIZ Live Stream - Person Detection", display_frame)
        
        # Nhấn 'q' để thoát
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
        # Nhẹ CPU
        time.sleep(0.001)

finally:
    # Dọn dẹp
    stop_threads = True
    capture_thread.join(timeout=1.0)
    detection_thread.join(timeout=1.0)
    cap.release()
    cv2.destroyAllWindows()
    print("Đã đóng chương trình")
