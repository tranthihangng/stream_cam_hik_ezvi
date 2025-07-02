# Camera Stream with Person Detection

Ứng dụng phát hiện người từ camera IP Hikvision/EZVIZ sử dụng YOLOv8.

## Tính năng

- Kết nối với camera IP Hikvision/EZVIZ qua RTSP
- Phát hiện người trong thời gian thực
- Hiển thị số lượng người và độ tin cậy
- Tối ưu hóa hiệu suất với đa luồng
- Hiển thị FPS camera và FPS detection

## Cài đặt

```bash
# Clone repository
git clone https://github.com/tranthihangng/stream_cam_hik_ezvi.git
cd stream_cam_hik_ezvi

# Cài đặt thư viện
pip install opencv-python
pip install ultralytics
```

## Sử dụng

1. Cập nhật thông tin camera trong file `ezviz/gui.py`:
   ```python
   rtsp_url = "rtsp://admin:PASSWORD@IP_ADDRESS:554/h264/ch1/sub/av_stream"
   ```

2. Chạy ứng dụng:
   ```bash
   python ezviz/gui.py
   ```

3. Nhấn phím 'q' để thoát.

## Cấu trúc thư mục

```
stream_cam_hik_ezvi/
├── ezviz/
│   ├── gui.py           # Ứng dụng chính với YOLOv8
│   └── frame.py         # Ứng dụng xử lý frame đơn giản
├── .gitignore
└── README.md
```

## Yêu cầu

- Python 3.8+
- OpenCV
- Ultralytics YOLOv8
- Camera IP Hikvision/EZVIZ với RTSP

# MVS-camera



# Run instuctions
MVS installer needs to be installed and IP address of the camera needs to be corrected before running this code.  


the camera dll is provided in this repository. however, it can also be found in this location after installing the MVS installer.

"C:/Program Files (x86)/Common Files/MVS/Runtime/Win64_x64/MvCameraControl.dll"


run the BasicDemo.py
an opencv window will appear with a video stream from the camera. 
