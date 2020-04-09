"""
getNumberCameras.py

Simple sample application demostrating the use of the getNumberCameras function 
in the pixelinkWrapper.
"""
from pixelinkWrapper import*


def main():
    
    #
    #  Call getNumberCameras to see not only how many Pixelink cameras
    #  are connected to this system, but to get connection information on
    #  each of the cameras found
    #
    #  Like all pixelinkWrapper functions, getNumberCameras returns a tuple with
    #  a number of elements. More specifically, getNumberCameras will return: 
    #     ret[0] - Return code
    #     ret[1] - A list of PxLApi._CameraIdInfo(s), with an element for each camera found
    ret = PxLApi.getNumberCameras()
    if PxLApi.apiSuccess(ret[0]):
      
      # The list of cameras found is actually a list of PxLApi._CameraIdInfo(s). See the
      # Pixelink API documentation for details on each of the fields in the CAMERA_ID_INFO
      cameras = ret[1]
      print ("Found %d Cameras:" % len(cameras))
      for i in range(len(cameras)):
        print("  Serial number - %d" % cameras[i].CameraSerialNum)
    else:
      print ("getNumberCameras return code: %d" % ret[0])

if __name__ == "__main__":
    main()
