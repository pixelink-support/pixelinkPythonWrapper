"""
getHDRSnapshot.py

Sample code to capture images from an HDR Pixelink camera and save each encoded image to a file.
"""

from pixelinkWrapper import*
from ctypes import*
import os
import sys

SUCCESS = 0
FAILURE = 1

# If the user specifies a name on the command line, we'll use that as the filename,
# otherwise use a default name.
PARM_EXE_NAME = 0
PARM_FILENAME = 1

"""
Check if gain HDR is supported by a camera.
If gain HDR is supported, this is an HDR camera.

Returns TRUE if it is the HDR camera
"""
def does_camera_support_hdr(hCamera):

    assert 0 != hCamera

    # Read the gain HDR feature information
    ret = PxLApi.getCameraFeatures(hCamera, PxLApi.FeatureId.GAIN_HDR)
    if PxLApi.apiSuccess(ret[0]):
        cameraFeatures = ret[1]
            
        # Do a few sanity checks
        assert 1 == cameraFeatures.uNumberOfFeatures                                # We only asked about one feature...
        assert PxLApi.FeatureId.GAIN_HDR == cameraFeatures.Features[0].uFeatureId    # ... and that feature is gain HDR        
        # Is the gian HDR feature supported?
        isSupported = ((cameraFeatures.Features[0].uFlags & PxLApi.FeatureFlags.PRESENCE) != 0)
    
    return isSupported

"""
Set gain HDR mode to "Camera HDR" or "Interleaved HDR"
 
Returns SUCCESS or FAILURE
"""
def set_hdr_mode(hCamera, hdrMode):

    assert 0 != hCamera
    
    # Set gain HDR mode to "Camera HDR" or "Interleaved HDR".
    # Disable gain HDR mode on default.
    if PxLApi.GainHdr.CAMERA == hdrMode:
        # Set gain HDR mode to "Camera HDR"
        flags = PxLApi.FeatureFlags.MANUAL
        params = [PxLApi.GainHdr.CAMERA,]
    elif PxLApi.GainHdr.INTERLEAVED == hdrMode:
        # Set gain HDR mode to "Interleaved HDR"
        flags = PxLApi.FeatureFlags.MANUAL
        params = [PxLApi.GainHdr.INTERLEAVED,]
    else:
        # Disable gain HDR mode
        flags = PxLApi.FeatureFlags.OFF
        params = [0,]

    ret = PxLApi.setFeature(hCamera, PxLApi.FeatureId.GAIN_HDR, flags, params)
    if not PxLApi.apiSuccess(ret[0]):
        return FAILURE

    return SUCCESS

"""
Get a snapshot from the camera, and save to a file
 
Returns SUCCESS or FAILURE
"""
def get_hdr_snapshot(hCamera, imageFormat, fileName):

    assert 0 != hCamera
    assert 0 <= imageFormat
    assert None != fileName

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
            
            assert 0 != len(rawImage)
            assert frameDescriptor
            #
            # Do any image processing here
            #                      

            # Encode the raw image into something displayable
            ret = PxLApi.formatImage(rawImage, frameDescriptor, imageFormat)
            if SUCCESS == ret[0]:
                formatedImage = ret[1]
                # Save formated image into a file
                if save_image_to_file(fileName, formatedImage) == SUCCESS:
                    return SUCCESS

    return FAILURE

"""
Query the camera for region of interest (ROI), decimation, and pixel format, and gain HDR mode.
Using this information, we can calculate the size of a raw image.

Returns 0 on failure
"""
def determine_raw_image_size(hCamera):

    assert 0 != hCamera

    # Get region of interest (ROI)
    ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.ROI)
    if not PxLApi.apiSuccess(ret[0]):
        return 0
    params = ret[2]
    roiWidth = params[PxLApi.RoiParams.WIDTH]
    roiHeight = params[PxLApi.RoiParams.HEIGHT]

    # Query pixel addressing
    ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.PIXEL_ADDRESSING)
    if not PxLApi.apiSuccess(ret[0]):
        return 0
    params = ret[2]

    # Width and height factor by which the image is reduced
    pixelAddressingValueX = params[PxLApi.PixelAddressingParams.X_VALUE]
    pixelAddressingValueY = params[PxLApi.PixelAddressingParams.Y_VALUE]

    # We can calulate the number of pixels now.
    numPixels = (roiWidth / pixelAddressingValueX) * (roiHeight / pixelAddressingValueY)

    # Knowing pixel format means we can determine how many bytes per pixel.
    ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.PIXEL_FORMAT)
    if not PxLApi.apiSuccess(ret[0]):
        return 0
    params = ret[2]
    pixelFormat = int(params[0])

    # And now the size of the frame
    pixelSize = PxLApi.getBytesPerPixel(pixelFormat)
    frameSize = int(numPixels * pixelSize)

    # Check which gain HDR mode the camera is using
    ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.GAIN_HDR)
    if not PxLApi.apiSuccess(ret[0]):
        return 0
    params = ret[2]
    # If the camera is using the interleaved HDR mode, double the size of the raw image
    if PxLApi.GainHdr.INTERLEAVED == params[0]:
        return frameSize * 2

    return frameSize

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
        ret = PxLApi.getNextFrame(hCamera, rawImage)
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
    if not os.path.exists("getHDRSnapshot"):
        os.makedirs("getHDRSnapshot")

    filepath = "getHDRSnapshot/" + fileName
    # Open a file for binary write
    file = open(filepath, "wb")
    if None == file:
        return FAILURE
    numBytesWritten = file.write(formatedImage)
    file.close()

    if numBytesWritten == len(formatedImage):
        return SUCCESS

    return FAILURE


def main():
    
    fileRoot = "snapshot"
    fileEnding = ("CameraHdr.bmp", "InterleavedHdr.bmp")
    fileName = ""

    # Did the user specify a filename to use?
    if len(sys.argv) > PARM_FILENAME:
        fileRoot = sys.argv[PARM_FILENAME]

    # Tell the camera we want to start using it.
	# NOTE: We're assuming there's only one camera.
    ret = PxLApi.initialize(0)
    if not PxLApi.apiSuccess(ret[0]):
        return FAILURE
    hCamera = ret[1]

    # Check whether the connected camera is an HDR camera.
    if not does_camera_support_hdr(hCamera):
        PxLApi.uninitialize(hCamera)
        print("This is not an HDR camera.")
        return FAILURE

    # Get a snapshot for each gain HDR mode
    for index in range(PxLApi.GainHdr.INTERLEAVED):
        fileNameSelect = index
        hdrMode = index + 1

        # Set gain HDR mode to "Camera HDR" or "Interleaved HDR"
        if set_hdr_mode(hCamera, hdrMode) == FAILURE:
            PxLApi.uninitialize(hCamera)
            return FAILURE

        # Prepare a snapshot file name for each HDR mode
        fileName = fileRoot + fileEnding[fileNameSelect]
        
        # Get a snapshot for each gian HDR mode and save it to a file
        retVal = get_hdr_snapshot(hCamera, PxLApi.ImageFormat.BMP, fileName)
        if SUCCESS == retVal:
            print("Saved image to 'getHDRSnapshot/%s'" % fileName)
        else:
            print("ERROR: Unable to capture an image")

    # Don't leave HDR on
    set_hdr_mode(hCamera, PxLApi.GainHdr.NONE)

    # Tell the camera we're done with it.
    PxLApi.uninitialize(hCamera)

    if SUCCESS != retVal:
        return FAILURE

    return SUCCESS


if __name__ == "__main__":
    main()
