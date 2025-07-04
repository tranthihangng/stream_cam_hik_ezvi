import cv2
import time
import sys

# RTSP URL
rtsp_url = "rtsp://admin:LCGSXD@192.168.1.177:554/h264/ch1/sub/av_stream"

print("🔍 Testing RTSP connection...")
print(f"URL: {rtsp_url}")

# Try to connect
cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)

# Set properties for better performance
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
cap.set(cv2.CAP_PROP_FPS, 10)  # Lower FPS for testing
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('H', '2', '6', '4'))

if not cap.isOpened():
    print("❌ Failed to connect to camera!")
    print("\n💡 Troubleshooting tips:")
    print("1. Check if the IP address is correct")
    print("2. Verify the password")
    print("3. Make sure the camera is powered on")
    print("4. Check network connectivity")
    print("5. Try pinging the camera IP")
    sys.exit(1)

print("✅ Camera connected successfully!")

# Test reading frames
frame_count = 0
start_time = time.time()
max_frames = 30  # Test for 30 frames

print("📹 Testing frame capture...")

try:
    while frame_count < max_frames:
        ret, frame = cap.read()
        
        if ret and frame is not None:
            frame_count += 1
            print(f"✅ Frame {frame_count}/{max_frames} captured - Size: {frame.shape}")
            
            # Show the frame
            cv2.imshow("Test Connection", frame)
            
            # Press 'q' to quit early
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            print(f"❌ Failed to read frame {frame_count + 1}")
            break
        
        time.sleep(0.1)  # Small delay

except KeyboardInterrupt:
    print("\n👋 Interrupted by user")
except Exception as e:
    print(f"❌ Error: {e}")

finally:
    # Calculate FPS
    elapsed_time = time.time() - start_time
    if elapsed_time > 0:
        fps = frame_count / elapsed_time
        print(f"\n📊 Results:")
        print(f"   Frames captured: {frame_count}")
        print(f"   Time elapsed: {elapsed_time:.2f} seconds")
        print(f"   Average FPS: {fps:.2f}")
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    print("✅ Test completed") 