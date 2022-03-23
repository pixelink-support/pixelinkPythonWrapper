"""
getNumPySnapshot.py

Sample code to capture an image from a Pixelink camera and save the encoded image to folder as a file.  This code
is very similiar with the getSnappshot sample, but a NumPy 2D array is used for the image buffer
"""

from pixelinkWrapper import*
from ctypes import*
import os
import numpy as np

SUCCESS = 0
FAILURE = 1

"""
Get a snapshot from the camera, and save to a file.
"""
def get_snapshot(hCamera, imageFormat, fileName):

    assert 0 != hCamera
    assert fileName
    
    # Determine the size of buffer we'll need to hold an image from the camera
    width, height, bytesPerPixel = determine_raw_image_size(hCamera)
    if 0 == width or 0 == height:
        return FAILURE

    # Create a buffer to hold the raw image
    npImage = np.zeros([height,width*bytesPerPixel], dtype=np.uint8)

    if 0 != len(npImage):
        # Capture a NumPy image.  
        ret = get_np_image(hCamera, npImage)
        if PxLApi.apiSuccess(ret[0]):
            frameDescriptor = ret[1]
            
            assert 0 != len(npImage)
            assert frameDescriptor
            #
            # Do any image processing here
            #
            # just for fun -- we will saturate the middle 20% of the image
            startRow = int((height/5)*2)
            endRow = int((height/5)*3)
            startCol = int(((width*bytesPerPixel)/5)*2)
            endCol = int(((width*bytesPerPixel)/5)*3)

            npImage[startRow:endRow,startCol:endCol] = 0xff
            
            # Encode the raw image into something displayable
            ret = PxLApi.formatNumPyImage(npImage, frameDescriptor, imageFormat)
            if SUCCESS == ret[0]:
                formatedImage = ret[1]
                # Save formated image into a file
                if save_image_to_file(fileName, formatedImage) == SUCCESS:
                    return SUCCESS
            
    return FAILURE

"""
Query the camera for region of interest (ROI), decimation, and pixel format
Using this information, we can calculate the size of a raw image

Returns 0 on failure
"""
def determine_raw_image_size(hCamera):

    assert 0 != hCamera

    roiWidth = 0
    roiHeight = 0

    # Get region of interest (ROI)
    ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.ROI)
    if PxLApi.apiSuccess(ret[0]):
        params = ret[2]
        roiWidth = params[PxLApi.RoiParams.WIDTH]
        roiHeight = params[PxLApi.RoiParams.HEIGHT]

    # Query pixel addressing
        # assume no pixel addressing (in case it is not supported)
    pixelAddressingValueX = 1
    pixelAddressingValueY = 1

    ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.PIXEL_ADDRESSING)
    if PxLApi.apiSuccess(ret[0]):
        params = ret[2]
        if PxLApi.PixelAddressingParams.NUM_PARAMS == len(params):
            # Camera supports symmetric and asymmetric pixel addressing
            pixelAddressingValueX = params[PxLApi.PixelAddressingParams.X_VALUE]
            pixelAddressingValueY = params[PxLApi.PixelAddressingParams.Y_VALUE]
        else:
            # Camera supports only symmetric pixel addressing
            pixelAddressingValueX = params[PxLApi.PixelAddressingParams.VALUE]
            pixelAddressingValueY = params[PxLApi.PixelAddressingParams.VALUE]

    # We can calulate the number of pixels now.
    numPixels = (roiWidth / pixelAddressingValueX) * (roiHeight / pixelAddressingValueY)
    ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.PIXEL_FORMAT)

    # Knowing pixel format means we can determine how many bytes per pixel.
    params = ret[2]
    pixelFormat = int(params[0])

    # And now the size of the frame
    pixelSize = PxLApi.getBytesPerPixel(pixelFormat)

    return ( int(roiWidth / pixelAddressingValueX),  # width inn pixels
             int(roiHeight / pixelAddressingValueY), # height in pixels
             pixelSize)                              # number of bytes / pixel
"""
Capture an image from the camera. 
 
NOTE: PxLApi.getNextNumPyFrame is a blocking call. 
i.e. PxLApi.getNextNumPyFrame won't return until an image is captured.
So, if you're using hardware triggering, it won't return until the camera is triggered.

Returns a return code with success and frame descriptor information or API error
"""
def get_np_image(hCamera, npImage):

    assert 0 != hCamera
    assert 0 != len(npImage)

    MAX_NUM_TRIES = 4

    # Put camera into streaming state so we can capture an image
    ret = PxLApi.setStreamState(hCamera, PxLApi.StreamState.START)
    if not PxLApi.apiSuccess(ret[0]):
        return FAILURE
      
    # Get an image
    # NOTE: PxLApi.getNextFrame can return ApiCameraTimeoutError on occasion.
    # How you handle this depends on your situation and how you use your camera. 
    # For this sample app, we'll just retry a few times.
    ret = (PxLApi.ReturnCode.ApiUnknownError,)

    for i in range(MAX_NUM_TRIES):
        ret = PxLApi.getNextNumPyFrame(hCamera, npImage)
        if PxLApi.apiSuccess(ret[0]):
            break

    # Done capturing, so no longer need the camera streaming images.
    # Note: If ret is used for this call, it will lose frame descriptor information.
    PxLApi.setStreamState(hCamera, PxLApi.StreamState.STOP)

    return ret

"""
Save the encoded image buffer to a file
This overwrites any existing file

Returns SUCCESS or FAILURE
"""
def save_image_to_file(fileName, formatedImage):
    
    assert fileName
    assert 0 != len(formatedImage)

    # Create a folder to save snapshots if it does not exist 
    if not os.path.exists("getSnapshot"):
        os.makedirs("getSnapshot")

    filepass = "getSnapshot/" + fileName
    # Open a file for binary write
    file = open(filepass, "wb")
    if None == file:
        return FAILURE
    numBytesWritten = file.write(formatedImage)
    file.close()

    if numBytesWritten == len(formatedImage):
        return SUCCESS

    return FAILURE


def main():
    
    filenameJpeg = "snapshot.jpg"
    filenameBmp = "snapshot.bmp"
    filenameTiff = "snapshot.tiff"
    filenamePsd = "snapshot.psd"
    filenameRgb24 = "snapshot.rgb24.bin"
    filenameRgb24Nondib = "snapshot.rgb24nondib.bin"
    filenameRgb48 = "snapshot.rgb48.bin"
    filenameMono8 = "snapshot.mono8.bin"

    # Tell the camera we want to start using it.
	# NOTE: We're assuming there's only one camera.
    ret = PxLApi.initialize(0)
    if not PxLApi.apiSuccess(ret[0]):
        return 1
    hCamera = ret[1]

    # Get a snapshot and save it to a folder as a file
    retVal = get_snapshot(hCamera, PxLApi.ImageFormat.JPEG, filenameJpeg)
    if SUCCESS == retVal:
        print("Saved image to 'getSnapshot/%s'" % filenameJpeg)
        retVal = get_snapshot(hCamera, PxLApi.ImageFormat.BMP, filenameBmp)
        if SUCCESS == retVal:
            print("Saved image to 'getSnapshot/%s'" % filenameBmp)
            retVal = get_snapshot(hCamera, PxLApi.ImageFormat.TIFF, filenameTiff)
            if SUCCESS == retVal:
                print("Saved image to 'getSnapshot/%s'" % filenameTiff)
                retVal = get_snapshot(hCamera, PxLApi.ImageFormat.PSD, filenamePsd)
                if SUCCESS == retVal:
                    print("Saved image to 'getSnapshot/%s'" % filenamePsd)
                    retVal = get_snapshot(hCamera, PxLApi.ImageFormat.RAW_BGR24, filenameRgb24)
                    if SUCCESS == retVal:
                        print("Saved image to 'getSnapshot/%s'" % filenameRgb24)
                        retVal = get_snapshot(hCamera, PxLApi.ImageFormat.RAW_BGR24_NON_DIB, filenameRgb24Nondib)
                        if SUCCESS == retVal:
                            print("Saved image to 'getSnapshot/%s'" % filenameRgb24Nondib)
                            retVal = get_snapshot(hCamera, PxLApi.ImageFormat.RAW_RGB48, filenameRgb48)
                            if SUCCESS == retVal:
                                print("Saved image to 'getSnapshot/%s'" % filenameRgb48)
                                # Only capture MONO8 for monochrome cameras
                                """
                                retVal = get_snapshot(hCamera, PxLApi.ImageFormat.RAW_MONO8, filenameMono8)
                                if SUCCESS == retVal:
                                    print("Saved image to 'getSnapshot/%s'" % filenameMono8)
                                """

    # Tell the camera we're done with it.
    PxLApi.uninitialize(hCamera)

    if SUCCESS != retVal:
        print("ERROR: Unable to capture an image")
        return FAILURE

    return SUCCESS


if __name__ == "__main__":
    main()
