"""
getPolarSnapshot.py

Sample code to capture and save 4 encoded BMP images from a Pixelink polar camera; 
where each image represents each of the 4 polar channels.
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
Check if polar weightings are supported by a camera.
If polar weightings are supported, this is a polar camera.

Returns TRUE if it is the polar camera
"""
def is_polar_camera(hCamera):

    assert 0 != hCamera

    # Read the polar weightings feature information
    ret = PxLApi.getCameraFeatures(hCamera, PxLApi.FeatureId.POLAR_WEIGHTINGS)
    if PxLApi.apiSuccess(ret[0]):
        cameraFeatures = ret[1]
        
        # Do a few sanity checks
        assert 1 == cameraFeatures.uNumberOfFeatures                                # We only asked about one feature...
        assert PxLApi.FeatureId.POLAR_WEIGHTINGS == cameraFeatures.Features[0].uFeatureId    # ... and that feature is polar weightings
        
        # Is the polar weightings feature supported?
        isSupported = ((cameraFeatures.Features[0].uFlags & PxLApi.FeatureFlags.PRESENCE) != 0)
    
    return isSupported

"""
Set camera pixel format to Polar4_12

Returns SUCCESS or FAILURE
"""
def set_polar_pixel_format(hCamera):

    assert 0 != hCamera

    # Set pixel format to Polar4_12
    flags = PxLApi.FeatureFlags.MANUAL
    params = [PxLApi.PixelFormat.POLAR4_12,]
    ret = PxLApi.setFeature(hCamera, PxLApi.FeatureId.PIXEL_FORMAT, flags, params)
    if not PxLApi.apiSuccess(ret[0]):
        return FAILURE
    
    return SUCCESS

"""
Get a snapshot from the camera, and save to a file
 
Returns SUCCESS or FAILURE
"""
def get_polar_snapshot(hCamera, imageFormat, fileName, polarChannel):

    assert 0 != hCamera
    assert 0 <= imageFormat
    assert None != fileName
    assert 0 <= polarChannel

    # Set polar channels for a snapshot, where one polar channel has a weighting of 100%, and the others are 0.
    # If more than 4 snapshots taken, polar weighting for each polar channel is set to 100%.
    if PxLApi.PolarWeightings.WEIGHTINGS_0_DEG == polarChannel:
        polWeight0 = 100
        polWeight45 = 0
        polWeight90 = 0
        polWeight135 = 0
    elif PxLApi.PolarWeightings.WEIGHTINGS_45_DEG == polarChannel:
        polWeight0 = 0
        polWeight45 = 100
        polWeight90 = 0
        polWeight135 = 0
    elif PxLApi.PolarWeightings.WEIGHTINGS_90_DEG == polarChannel:
        polWeight0 = 0
        polWeight45 = 0
        polWeight90 = 100
        polWeight135 = 0
    elif PxLApi.PolarWeightings.WEIGHTINGS_135_DEG == polarChannel:
        polWeight0 = 0
        polWeight45 = 0
        polWeight90 = 0
        polWeight135 = 100
    else:
        polWeight0 = 100
        polWeight45 = 100
        polWeight90 = 100
        polWeight135 = 100

    # Set polar weightings for a snapshot
    if set_polar_weightings(hCamera, polWeight0, polWeight45, polWeight90, polWeight135) == FAILURE:
        return FAILURE

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
Set polar weighting for each polar channel
 
Returns SUCCESS or FAILURE
"""
def set_polar_weightings(hCamera, polWeight0, polWeight45, polWeight90, polWeight135):

    assert 0 != hCamera
    assert 0 <= polWeight0
    assert 0 <= polWeight45
    assert 0 <= polWeight90
    assert 0 <= polWeight135

    # Set polar weighting for each polar channel
    flags = PxLApi.FeatureFlags.MANUAL
    params = [polWeight0, polWeight45, polWeight90, polWeight135]
    ret = PxLApi.setFeature(hCamera, PxLApi.FeatureId.POLAR_WEIGHTINGS, flags, params)
    if PxLApi.apiSuccess(ret[0]):
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

    # We can calulate the number of pixels now.
    # Value of pixel addressing feature is not included into calculation since a polar camera does not support it.
    numPixels = roiWidth * roiHeight

    # Knowing pixel format means we can determine how many bytes per pixel.
    ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.PIXEL_FORMAT)
    if not PxLApi.apiSuccess(ret[0]):
        return 0
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
    if not os.path.exists("getPolarSnapshot"):
        os.makedirs("getPolarSnapshot")

    filepass = "getPolarSnapshot/" + fileName
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
    
    fileRoot = "snapshot"
    fileEnding = ("0deg.bmp", "45deg.bmp", "90deg.bmp", "135deg.bmp")
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

    # Check whether the polar camera is connected.
    if not is_polar_camera(hCamera):
        PxLApi.uninitialize(hCamera)
        print("This is not a polar camera.")
        return FAILURE

    # Set camera pixel format to Polar4_12
    if set_polar_pixel_format(hCamera) == FAILURE:
        PxLApi.uninitialize(hCamera)
        return FAILURE

    numOfPolarChannels = 4
    for polarChannel in range(numOfPolarChannels):
        
        # Prepare file name for each snapshot
        fileName = fileRoot + fileEnding[polarChannel]

        # Get a snapshot of each polar channel set, where one polar channel has a weighting of 100%, and the others are 0.
        # Save each image to a file
        retVal = get_polar_snapshot(hCamera, PxLApi.ImageFormat.BMP, fileName, polarChannel)
        if SUCCESS == retVal:
            print("Saved image to 'getPolarSnapshot/%s'" % fileName)
        else:
            print("ERROR: Unable to capture an image")

    # Tell the camera we're done with it.
    PxLApi.uninitialize(hCamera)

    if SUCCESS != retVal:
        return FAILURE

    return SUCCESS


if __name__ == "__main__":
    main()
