"""
getCameraInfo.py

Demonstration of a trivial interaction with the Pixelink API.

This demo program has minimal error handling, as its purpose is to show minimal code to interact with the Pixelink API,
not tell you how to do your error handling.

With this program, we assume that there is at least one camera connected, and that no cameras are connected or disconnected 
while the program is running.
"""

from pixelinkWrapper import*

"""
This function assumes there's only one camera connected.
"""
def print_info_for_one_camera():

    # Initialize a camera
    ret = PxLApi.initialize(0)
    if PxLApi.apiSuccess(ret[0]):
        hCamera = ret[1]
        ret = PxLApi.getCameraInfo(hCamera)
        if PxLApi.apiSuccess(ret[0]):
            cameraInfo = ret[1]
            print_camera_info(cameraInfo)
        # Uninitialize a camera
        PxLApi.uninitialize(hCamera)

"""
This will print information for all cameras connected and connectable.
"""
def print_info_for_all_cameras():

    # First: Determine how many cameras are connected and available for connecting
    ret = PxLApi.getNumberCameras()
    if PxLApi.apiSuccess(ret[0]):
        cameraIdInfo = ret[1]
        numCameras = len(cameraIdInfo)
        if 0 < numCameras:
            # One-by-one, get the camera info for each camera
            for i in range(numCameras):
                serialNumber = cameraIdInfo[i].CameraSerialNum
                # Connect to the camera
                ret = PxLApi.initialize(serialNumber)
                if PxLApi.apiSuccess(ret[0]):
                    hCamera = ret[1]
                    # And get the info
                    ret = PxLApi.getCameraInfo(hCamera)
                    if PxLApi.apiSuccess(ret[0]):
                        cameraInfo = ret[1]
                        print("\nCamera %i of %i (serialNumber %i):" % (i+1, numCameras, serialNumber))
                        print_camera_info(cameraInfo)
                    
                    # Don't forget to tell the camera we're done, so that we don't use any camera-related resources.							 
                    PxLApi.uninitialize(hCamera)

"""
Print all the info for the camera
"""
def print_camera_info(cameraInfo):
    
    print("Name -------------- '%s'" % cameraInfo.CameraName.decode("utf-8"))
    print("Description ------- '%s'" % cameraInfo.Description.decode("utf-8"))
    print("Vendor Name ------- '%s'" % cameraInfo.VendorName.decode("utf-8"))
    print("Serial Number ----- '%s'" % cameraInfo.SerialNumber.decode("utf-8"))
    print("Firmware Version -- '%s'" % cameraInfo.FirmwareVersion.decode("utf-8"))
    print("FPGA Version ------ '%s'" % cameraInfo.FPGAVersion.decode("utf-8"))
    print("XML Version ------- '%s'" % cameraInfo.XMLVersion.decode("utf-8"))
    print("Bootload Version -- '%s'" % cameraInfo.BootloadVersion.decode("utf-8"))
    print("Model Name -------- '%s'" % cameraInfo.ModelName.decode("utf-8"))
    print("Lens Description -- '%s'" % cameraInfo.LensDescription.decode("utf-8"))


def main():
    
    # We assume there's only one camera
    print_info_for_one_camera()

    # You can uncomment this to see how to get information for all cameras
    # print_info_for_all_cameras()

    return 0


if __name__ == "__main__":
    main()
