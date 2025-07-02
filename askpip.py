from MvCameraControl_class import *
from MvCameraControl_class import *
from PixelType_header import *
from PixelType_const import *
from MvErrorDefine_const import *
from CameraParams_const import *
from CameraParams_header import *
deviceList = MV_CC_DEVICE_INFO_LIST()
ret = MvCamera.MV_CC_EnumDevices(MV_GIGE_DEVICE, deviceList)
print("Number of cameras found:", deviceList.nDeviceNum)

for i in range(deviceList.nDeviceNum):
    info = deviceList.pDeviceInfo[i].SpecialInfo.stGigEInfo
    ip = "{}.{}.{}.{}".format(
        (info.nCurrentIp >> 24) & 0xFF,
        (info.nCurrentIp >> 16) & 0xFF,
        (info.nCurrentIp >> 8) & 0xFF,
        info.nCurrentIp & 0xFF
    )
    print(f"Camera {i} IP:", ip)
