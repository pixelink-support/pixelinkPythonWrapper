"""
getMultipleSnapshots.py

Sample code to capture images from a Pixelink camera and save the encoded images to a folder as files.
"""

from pixelinkWrapper import*
from ctypes import*
import os
import time

SUCCESS = 0
FAILURE = 1

"""
Get a snapshot from the camera, and save it to a file.
"""
def get_snapshot(hCamera, imageFormat, fileName):

    assert 0 != hCamera
    assert fileName
    
    # Determine the size of buffer we'll need to hold an image from the camera
    rawImageSize = determine_raw_image_size(hCamera)
    if 0 == rawImageSize:
        return FAILURE

    # Create a buffer to hold the raw image
    rawImage = create_string_buffer(rawImageSize)

    if 0 != len(rawImage):
        # Capture a raw image. The raw image buffer will contain image data on success. 
        ret = get_raw_image(hCamera, rawImage)
        if PxLApi.apiSuccess(ret[0]):
            frameDescriptor = ret[1]
            #
            # Do any image processing here
            #
            
            assert 0 != len(rawImage)
            assert frameDescriptor
            # Encode the raw image into something displayable
            ret = PxLApi.formatImage(rawImage, frameDescriptor, imageFormat)
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

    # Get region of interest (ROI)
    ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.ROI)
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

    return int(numPixels * pixelSize)

"""
Capture an image from the camera.
 
NOTE: PxLApi.getNextFrame is a blocking call. 
i.e. PxLApi.getNextFrame won't return until an image is captured.
So, if you're using hardware triggering, it won't return until the camera is triggered.

Returns a return code with success and frame descriptor information or API error
"""
def get_raw_image(hCamera, rawImage):

    assert 0 != hCamera
    assert 0 != len(rawImage)

    MAX_NUM_TRIES = 4

    # Get an image
    # NOTE: PxLApi.getNextFrame can return ApiCameraTimeoutError on occasion.
    # How you handle this depends on your situation and how you use your camera. 
    # For this sample app, we'll just retry a few times.
    ret = (PxLApi.ReturnCode.ApiUnknownError,)

    for i in range(MAX_NUM_TRIES):
        ret = PxLApi.getNextFrame(hCamera, rawImage)
        if PxLApi.apiSuccess(ret[0]):
            break

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
    if not os.path.exists("getMultipleSnapshots"):
        os.makedirs("getMultipleSnapshots")

    filepass = "getMultipleSnapshots/" + fileName
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

    # Tell the camera we want to start using it.
	# NOTE: We're assuming there's only one camera.
    ret = PxLApi.initialize(0)
    if not PxLApi.apiSuccess(ret[0]):
        return 1
    hCamera = ret[1]

    # Put camera into streaming state so we can capture an image
    ret = PxLApi.setStreamState(hCamera, PxLApi.StreamState.START)
    if not PxLApi.apiSuccess(ret[0]):
        return 1

    # Get the snapshots and save them to a folder as files
    for i in range(5):
        filenamePng = "image" + str(i) + ".png"
        retVal = get_snapshot(hCamera, PxLApi.ImageFormat.PNG, filenamePng)
        if SUCCESS == retVal:
            print("Saved image to 'getMultipleSnapshots/%s'" % filenamePng)
        else:
            print("Could not save image to 'getMultipleSnapshots/%s'" % filenamePng)
        time.sleep(2)

    # Done capturing, so no longer need the camera streaming images.
    # Note: If ret is used for this call, it will lose frame descriptor information.
    ret = PxLApi.setStreamState(hCamera, PxLApi.StreamState.STOP)
    if not PxLApi.apiSuccess(ret[0]):
        return 1

    # Tell the camera we're done with it.
    PxLApi.uninitialize(hCamera)

    if SUCCESS != retVal:
        return 1

    return 0


if __name__ == "__main__":
    main()
