import cv2
import time

# Khởi tạo stream từ camera EZVIZ
rtsp_url = "rtsp://admin:LCGSXD@192.168.1.177:554/h264/ch1/sub/av_stream"
cap = cv2.VideoCapture(rtsp_url)

if not cap.isOpened():
    print("❌ Không thể kết nối camera! Kiểm tra lại IP/RTSP URL.")
    exit()

# Đo FPS thực tế
frame_count = 0
start_time = time.time()

while True:
    ret, frame = cap.read()
    if not ret:
        print("⚠️ Không đọc được frame, thử lại…")
        break

    frame_count += 1

    cv2.imshow("EZVIZ - Gốc", frame)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)
    cv2.imshow("EZVIZ - Nhị phân", binary)

    # Tính FPS mỗi 5 giây
    if time.time() - start_time >= 5:
        fps = frame_count / (time.time() - start_time)
        print(f"📸 FPS thực tế: {fps:.2f} frames/second")
        frame_count = 0
        start_time = time.time()

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
