import cv2

# Địa chỉ RTSP camera EZVIZ
rtsp_url = "rtsp://admin:LCGSXD@192.168.1.177:554/h264/ch1/sub/av_stream"

cap = cv2.VideoCapture(rtsp_url)

if not cap.isOpened():
    print("❌ Không thể kết nối camera! Kiểm tra lại IP/RTSP URL.")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("⚠️ Không đọc được frame, thử lại…")
        break

    # ===== Hiển thị frame gốc =====
    cv2.imshow("EZVIZ - Gốc", frame)

    # ===== Xử lý nhị phân ảnh =====
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)           # Chuyển ảnh sang xám
    _, binary = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)  # Ngưỡng 100

    cv2.imshow("EZVIZ - Nhị phân", binary)

    # Nhấn 'q' để thoát
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
