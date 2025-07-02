import sys
import numpy as np
import cv2
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QComboBox, QSlider, QGroupBox, QMessageBox,
                            QStatusBar, QSpinBox, QDoubleSpinBox)
from PyQt5.QtGui import QPixmap, QImage, QFont
from PyQt5.QtCore import QTimer, Qt, pyqtSlot
from ctypes import c_ubyte, sizeof, byref, c_int, cast, POINTER, cdll
import time
import os

# Import all necessary modules for Hikrobot camera
from MvCameraControl_class import *
from PixelType_header import *
from PixelType_const import *
from MvErrorDefine_const import *
from CameraParams_const import *
from CameraParams_header import *

class HikRobotCameraGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Camera variables
        self.cam = None
        self.deviceList = None
        self.frame_count = 0
        self.is_capturing = False
        self.save_path = "captured_images"
        
        # Create save directory if it doesn't exist
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)
        
        # Setup UI
        self.setWindowTitle("Hikrobot Camera Viewer")
        self.setMinimumSize(1000, 700)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create top layout for camera controls
        top_layout = QHBoxLayout()
        main_layout.addLayout(top_layout)
        
        # Create camera selection group
        camera_group = QGroupBox("Camera Selection")
        camera_layout = QVBoxLayout(camera_group)
        
        # Camera dropdown and refresh button
        self.camera_combo = QComboBox()
        self.refresh_btn = QPushButton("Refresh Cameras")
        self.refresh_btn.clicked.connect(self.refresh_cameras)
        
        camera_layout.addWidget(QLabel("Select Camera:"))
        camera_layout.addWidget(self.camera_combo)
        camera_layout.addWidget(self.refresh_btn)
        
        # Connect button
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.connect_camera)
        camera_layout.addWidget(self.connect_btn)
        
        # Disconnect button
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.clicked.connect(self.disconnect_camera)
        self.disconnect_btn.setEnabled(False)
        camera_layout.addWidget(self.disconnect_btn)
        
        top_layout.addWidget(camera_group)
        
        # Create camera settings group
        settings_group = QGroupBox("Camera Settings")
        settings_layout = QVBoxLayout(settings_group)
        
        # Exposure control
        exposure_layout = QHBoxLayout()
        exposure_layout.addWidget(QLabel("Exposure (μs):"))
        self.exposure_spinbox = QDoubleSpinBox()
        self.exposure_spinbox.setRange(10, 1000000)
        self.exposure_spinbox.setValue(20000)
        self.exposure_spinbox.setSingleStep(1000)
        self.exposure_spinbox.setEnabled(False)
        exposure_layout.addWidget(self.exposure_spinbox)
        self.exposure_btn = QPushButton("Set")
        self.exposure_btn.clicked.connect(self.set_exposure)
        self.exposure_btn.setEnabled(False)
        exposure_layout.addWidget(self.exposure_btn)
        settings_layout.addLayout(exposure_layout)
        
        # Gain control
        gain_layout = QHBoxLayout()
        gain_layout.addWidget(QLabel("Gain:"))
        self.gain_spinbox = QDoubleSpinBox()
        self.gain_spinbox.setRange(0, 100)
        self.gain_spinbox.setValue(10)
        self.gain_spinbox.setSingleStep(1)
        self.gain_spinbox.setEnabled(False)
        gain_layout.addWidget(self.gain_spinbox)
        self.gain_btn = QPushButton("Set")
        self.gain_btn.clicked.connect(self.set_gain)
        self.gain_btn.setEnabled(False)
        gain_layout.addWidget(self.gain_btn)
        settings_layout.addLayout(gain_layout)
        
        # Pixel format selection
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Pixel Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["Mono8", "BGR8"])
        self.format_combo.setEnabled(False)
        format_layout.addWidget(self.format_combo)
        self.format_btn = QPushButton("Set")
        self.format_btn.clicked.connect(self.set_pixel_format)
        self.format_btn.setEnabled(False)
        format_layout.addWidget(self.format_btn)
        settings_layout.addLayout(format_layout)
        
        top_layout.addWidget(settings_group)
        
        # Create capture controls group
        capture_group = QGroupBox("Capture Controls")
        capture_layout = QVBoxLayout(capture_group)
        
        # Start/Stop streaming
        self.stream_btn = QPushButton("Start Streaming")
        self.stream_btn.setEnabled(False)
        self.stream_btn.clicked.connect(self.toggle_streaming)
        capture_layout.addWidget(self.stream_btn)
        
        # Capture single frame
        self.capture_btn = QPushButton("Capture Frame")
        self.capture_btn.setEnabled(False)
        self.capture_btn.clicked.connect(self.capture_frame)
        capture_layout.addWidget(self.capture_btn)
        
        top_layout.addWidget(capture_group)
        
        # Create image display area
        self.image_label = QLabel("No camera connected")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: black; color: white; font-size: 20px;")
        self.image_label.setMinimumSize(800, 500)
        main_layout.addWidget(self.image_label)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Timer for updating frames
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        
        # Initialize camera list
        self.refresh_cameras()
    
    def refresh_cameras(self):
        self.camera_combo.clear()
        
        # Enumerate devices
        self.deviceList = MV_CC_DEVICE_INFO_LIST()
        ret = MvCamera.MV_CC_EnumDevices(MV_GIGE_DEVICE | MV_USB_DEVICE, self.deviceList)
        if ret != 0:
            QMessageBox.critical(self, "Error", f"Failed to enumerate devices: {ret}")
            return
        
        if self.deviceList.nDeviceNum == 0:
            self.status_bar.showMessage("No cameras found")
            return
        
        self.status_bar.showMessage(f"Found {self.deviceList.nDeviceNum} cameras")
        
        # Add cameras to combo box
        for i in range(self.deviceList.nDeviceNum):
            mvcc_dev_info = cast(self.deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
            if mvcc_dev_info.nTLayerType == MV_GIGE_DEVICE:
                # Get camera name
                model_name = ""
                for c in mvcc_dev_info.SpecialInfo.stGigEInfo.chModelName:
                    if c == 0:
                        break
                    model_name += chr(c)
                
                # Get IP address
                nip1 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0xff000000) >> 24)
                nip2 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x00ff0000) >> 16)
                nip3 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x0000ff00) >> 8)
                nip4 = (mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x000000ff)
                ip_address = f"{nip1}.{nip2}.{nip3}.{nip4}"
                
                self.camera_combo.addItem(f"{model_name} ({ip_address})", i)
            
            elif mvcc_dev_info.nTLayerType == MV_USB_DEVICE:
                # Get camera name
                model_name = ""
                for c in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chModelName:
                    if c == 0:
                        break
                    model_name += chr(c)
                
                self.camera_combo.addItem(f"{model_name} (USB)", i)
    
    def connect_camera(self):
        if self.camera_combo.count() == 0:
            QMessageBox.warning(self, "Warning", "No cameras available")
            return
        
        camera_index = self.camera_combo.currentData()
        
        # Create camera instance
        self.cam = MvCamera()
        
        # Select device and create handle
        stDeviceList = cast(self.deviceList.pDeviceInfo[camera_index], POINTER(MV_CC_DEVICE_INFO)).contents
        ret = self.cam.MV_CC_CreateHandle(stDeviceList)
        if ret != 0:
            QMessageBox.critical(self, "Error", f"Failed to create handle: {ret}")
            self.cam = None
            return
        
        # Open device
        ret = self.cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
        if ret != 0:
            QMessageBox.critical(self, "Error", f"Failed to open device: {ret}")
            self.cam.MV_CC_DestroyHandle()
            self.cam = None
            return
        
        # For GigE cameras, set packet size
        if stDeviceList.nTLayerType == MV_GIGE_DEVICE:
            nPacketSize = self.cam.MV_CC_GetOptimalPacketSize()
            if int(nPacketSize) > 0:
                ret = self.cam.MV_CC_SetIntValue("GevSCPSPacketSize", nPacketSize)
                if ret != 0:
                    self.status_bar.showMessage(f"Warning: Failed to set packet size: {ret}")
            
            # Set heartbeat timeout
            ret = self.cam.MV_CC_SetIntValue("GevHeartbeatTimeout", 5000)
            if ret != 0:
                self.status_bar.showMessage(f"Warning: Failed to set heartbeat timeout: {ret}")
        
        # Set trigger mode to off
        ret = self.cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_OFF)
        if ret != 0:
            self.status_bar.showMessage(f"Warning: Failed to set trigger mode: {ret}")
        
        # Update UI
        self.connect_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(True)
        self.stream_btn.setEnabled(True)
        self.capture_btn.setEnabled(True)
        self.exposure_spinbox.setEnabled(True)
        self.exposure_btn.setEnabled(True)
        self.gain_spinbox.setEnabled(True)
        self.gain_btn.setEnabled(True)
        self.format_combo.setEnabled(True)
        self.format_btn.setEnabled(True)
        
        self.status_bar.showMessage("Camera connected successfully")
        self.image_label.setText("Camera connected. Click 'Start Streaming' to view video.")
    
    def disconnect_camera(self):
        if self.is_capturing:
            self.toggle_streaming()
        
        if self.cam:
            # Stop grabbing
            ret = self.cam.MV_CC_StopGrabbing()
            if ret != 0:
                self.status_bar.showMessage(f"Warning: Failed to stop grabbing: {ret}")
            
            # Close device
            ret = self.cam.MV_CC_CloseDevice()
            if ret != 0:
                self.status_bar.showMessage(f"Warning: Failed to close device: {ret}")
            
            # Destroy handle
            ret = self.cam.MV_CC_DestroyHandle()
            if ret != 0:
                self.status_bar.showMessage(f"Warning: Failed to destroy handle: {ret}")
            
            self.cam = None
        
        # Update UI
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.stream_btn.setEnabled(False)
        self.capture_btn.setEnabled(False)
        self.exposure_spinbox.setEnabled(False)
        self.exposure_btn.setEnabled(False)
        self.gain_spinbox.setEnabled(False)
        self.gain_btn.setEnabled(False)
        self.format_combo.setEnabled(False)
        self.format_btn.setEnabled(False)
        
        self.image_label.setText("No camera connected")
        self.status_bar.showMessage("Camera disconnected")
    
    def toggle_streaming(self):
        if not self.is_capturing:
            # Start grabbing
            ret = self.cam.MV_CC_StartGrabbing()
            if ret != 0:
                QMessageBox.critical(self, "Error", f"Failed to start grabbing: {ret}")
                return
            
            self.timer.start(30)  # Update every 30ms (~33 FPS)
            self.is_capturing = True
            self.stream_btn.setText("Stop Streaming")
            self.status_bar.showMessage("Streaming started")
        else:
            # Stop grabbing
            self.timer.stop()
            ret = self.cam.MV_CC_StopGrabbing()
            if ret != 0:
                self.status_bar.showMessage(f"Warning: Failed to stop grabbing: {ret}")
            
            self.is_capturing = False
            self.stream_btn.setText("Start Streaming")
            self.status_bar.showMessage("Streaming stopped")
    
    def update_frame(self):
        if not self.cam or not self.is_capturing:
            return
        
        try:
            # Get payload size
            stParam = MVCC_INTVALUE()
            memset(byref(stParam), 0, sizeof(MVCC_INTVALUE))
            ret = self.cam.MV_CC_GetIntValue("PayloadSize", stParam)
            if ret != 0:
                self.status_bar.showMessage(f"Error: Failed to get payload size: {ret}")
                return
            
            nDataSize = stParam.nCurValue
            pData = (c_ubyte * nDataSize)()
            stFrameInfo = MV_FRAME_OUT_INFO_EX()
            memset(byref(stFrameInfo), 0, sizeof(stFrameInfo))
            
            ret = self.cam.MV_CC_GetOneFrameTimeout(pData, nDataSize, stFrameInfo, 1000)
            if ret == 0:
                self.frame_count += 1
                
                # Process image based on pixel format
                if stFrameInfo.enPixelType == PixelType_Gvsp_Mono8:
                    # 8-bit grayscale
                    data = np.frombuffer(pData, dtype=np.uint8, count=stFrameInfo.nWidth*stFrameInfo.nHeight)
                    image = data.reshape((stFrameInfo.nHeight, stFrameInfo.nWidth))
                    qt_image = QImage(image.data, stFrameInfo.nWidth, stFrameInfo.nHeight, 
                                     stFrameInfo.nWidth, QImage.Format_Grayscale8)
                
                elif stFrameInfo.enPixelType == PixelType_Gvsp_BGR8_Packed:
                    # BGR format
                    data = np.frombuffer(pData, dtype=np.uint8, count=stFrameInfo.nWidth*stFrameInfo.nHeight*3)
                    image = data.reshape((stFrameInfo.nHeight, stFrameInfo.nWidth, 3))
                    qt_image = QImage(image.data, stFrameInfo.nWidth, stFrameInfo.nHeight, 
                                     stFrameInfo.nWidth*3, QImage.Format_BGR888)
                
                else:
                    # Try default conversion for other formats
                    try:
                        if stFrameInfo.enPixelType == 17301514:  # Bayer format
                            data = np.frombuffer(pData, dtype=np.uint8, count=stFrameInfo.nWidth*stFrameInfo.nHeight)
                            image = data.reshape((stFrameInfo.nHeight, stFrameInfo.nWidth))
                            # Convert Bayer to RGB
                            image = cv2.cvtColor(image, cv2.COLOR_BayerGB2BGR)
                            qt_image = QImage(image.data, stFrameInfo.nWidth, stFrameInfo.nHeight, 
                                             stFrameInfo.nWidth*3, QImage.Format_BGR888)
                        else:
                            # Default to grayscale
                            data = np.frombuffer(pData, dtype=np.uint8, count=stFrameInfo.nWidth*stFrameInfo.nHeight)
                            image = data.reshape((stFrameInfo.nHeight, stFrameInfo.nWidth))
                            qt_image = QImage(image.data, stFrameInfo.nWidth, stFrameInfo.nHeight, 
                                             stFrameInfo.nWidth, QImage.Format_Grayscale8)
                    except Exception as e:
                        self.status_bar.showMessage(f"Error processing frame: {str(e)}")
                        return
                
                # Display the image
                pixmap = QPixmap.fromImage(qt_image)
                if not pixmap.isNull():
                    # Scale the pixmap to fit the label while maintaining aspect ratio
                    scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.image_label.setPixmap(scaled_pixmap)
                    
                    # Update status bar with frame info
                    if self.frame_count % 10 == 0:  # Update status every 10 frames
                        self.status_bar.showMessage(
                            f"Frame #{self.frame_count}: {stFrameInfo.nWidth}x{stFrameInfo.nHeight}, "
                            f"PixelType: {hex(stFrameInfo.enPixelType)}"
                        )
                else:
                    self.status_bar.showMessage("Error: Empty pixmap")
            else:
                self.status_bar.showMessage(f"Error getting frame: {ret}")
        
        except Exception as e:
            self.status_bar.showMessage(f"Error in update_frame: {str(e)}")
    
    def set_exposure(self):
        if not self.cam:
            return
        
        exposure = self.exposure_spinbox.value()
        ret = self.cam.MV_CC_SetFloatValue("ExposureTime", exposure)
        if ret != 0:
            self.status_bar.showMessage(f"Failed to set exposure: {ret}")
        else:
            self.status_bar.showMessage(f"Exposure set to {exposure} μs")
    
    def set_gain(self):
        if not self.cam:
            return
        
        gain = self.gain_spinbox.value()
        ret = self.cam.MV_CC_SetFloatValue("Gain", gain)
        if ret != 0:
            self.status_bar.showMessage(f"Failed to set gain: {ret}")
        else:
            self.status_bar.showMessage(f"Gain set to {gain}")
    
    def set_pixel_format(self):
        if not self.cam:
            return
        
        format_index = self.format_combo.currentIndex()
        if format_index == 0:  # Mono8
            pixel_format = PixelType_Gvsp_Mono8
        else:  # BGR8
            pixel_format = PixelType_Gvsp_BGR8_Packed
        
        ret = self.cam.MV_CC_SetEnumValue("PixelFormat", pixel_format)
        if ret != 0:
            self.status_bar.showMessage(f"Failed to set pixel format: {ret}")
        else:
            self.status_bar.showMessage(f"Pixel format set to {self.format_combo.currentText()}")
    
    def capture_frame(self):
        if not self.cam:
            return
        
        # If not streaming, start grabbing for a single frame
        was_not_streaming = False
        if not self.is_capturing:
            was_not_streaming = True
            ret = self.cam.MV_CC_StartGrabbing()
            if ret != 0:
                QMessageBox.critical(self, "Error", f"Failed to start grabbing: {ret}")
                return
        
        try:
            # Get payload size
            stParam = MVCC_INTVALUE()
            memset(byref(stParam), 0, sizeof(MVCC_INTVALUE))
            ret = self.cam.MV_CC_GetIntValue("PayloadSize", stParam)
            if ret != 0:
                self.status_bar.showMessage(f"Error: Failed to get payload size: {ret}")
                return
            
            nDataSize = stParam.nCurValue
            pData = (c_ubyte * nDataSize)()
            stFrameInfo = MV_FRAME_OUT_INFO_EX()
            memset(byref(stFrameInfo), 0, sizeof(stFrameInfo))
            
            ret = self.cam.MV_CC_GetOneFrameTimeout(pData, nDataSize, stFrameInfo, 1000)
            if ret == 0:
                # Process image based on pixel format
                if stFrameInfo.enPixelType == PixelType_Gvsp_Mono8:
                    # 8-bit grayscale
                    data = np.frombuffer(pData, dtype=np.uint8, count=stFrameInfo.nWidth*stFrameInfo.nHeight)
                    image = data.reshape((stFrameInfo.nHeight, stFrameInfo.nWidth))
                    
                    # Save image
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    filename = f"{self.save_path}/capture_{timestamp}.png"
                    cv2.imwrite(filename, image)
                    
                elif stFrameInfo.enPixelType == PixelType_Gvsp_BGR8_Packed:
                    # BGR format
                    data = np.frombuffer(pData, dtype=np.uint8, count=stFrameInfo.nWidth*stFrameInfo.nHeight*3)
                    image = data.reshape((stFrameInfo.nHeight, stFrameInfo.nWidth, 3))
                    
                    # Save image
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    filename = f"{self.save_path}/capture_{timestamp}.png"
                    cv2.imwrite(filename, image)
                
                else:
                    # Try default conversion for other formats
                    try:
                        if stFrameInfo.enPixelType == 17301514:  # Bayer format
                            data = np.frombuffer(pData, dtype=np.uint8, count=stFrameInfo.nWidth*stFrameInfo.nHeight)
                            image = data.reshape((stFrameInfo.nHeight, stFrameInfo.nWidth))
                            # Convert Bayer to RGB
                            image = cv2.cvtColor(image, cv2.COLOR_BayerGB2BGR)
                        else:
                            # Default to grayscale
                            data = np.frombuffer(pData, dtype=np.uint8, count=stFrameInfo.nWidth*stFrameInfo.nHeight)
                            image = data.reshape((stFrameInfo.nHeight, stFrameInfo.nWidth))
                        
                        # Save image
                        timestamp = time.strftime("%Y%m%d_%H%M%S")
                        filename = f"{self.save_path}/capture_{timestamp}.png"
                        cv2.imwrite(filename, image)
                        
                    except Exception as e:
                        self.status_bar.showMessage(f"Error processing frame: {str(e)}")
                        return
                
                self.status_bar.showMessage(f"Image saved to {filename}")
            else:
                self.status_bar.showMessage(f"Error getting frame: {ret}")
        
        except Exception as e:
            self.status_bar.showMessage(f"Error capturing frame: {str(e)}")
        
        finally:
            # If we started grabbing just for this capture, stop it
            if was_not_streaming:
                ret = self.cam.MV_CC_StopGrabbing()
                if ret != 0:
                    self.status_bar.showMessage(f"Warning: Failed to stop grabbing: {ret}")
    
    def closeEvent(self, event):
        # Clean up when closing the application
        if self.is_capturing:
            self.toggle_streaming()
        
        if self.cam:
            self.disconnect_camera()
        
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HikRobotCameraGUI()
    window.show()
    sys.exit(app.exec_()) 