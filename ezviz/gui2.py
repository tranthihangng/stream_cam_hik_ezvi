import cv2

# Thay mã xác thực (LCGSXD) và IP (192.168.1.177)
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

    cv2.imshow("EZVIZ Live Stream", frame)

    # Nhấn 'q' để thoát
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
