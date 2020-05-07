"""
openCVSnapshot.py

A demonstration of how to capture a camera image that can be 'imported' into openCV.

OpenCV needs to be installed to run this sample (e.g.: 'pip install opencv-python')
to locate the appropriate libaries.
"""

from pixelinkWrapper import*
from ctypes import*
import numpy
import cv2
import os

# A few useful defines
EXIT_SUCCESS = 0
EXIT_FAILURE = 1

PT_COLOR = 0
PT_MONO = 1
PT_OTHERWISE = 2 # Special cameras, like polarized and interleaved HDR

"""
IMPORTANT NOTE:
This function will only return a meaningful value, if called while NOT streaming
"""
def getPixelType(hCamera):

    pixelType = PT_OTHERWISE
    # Take a simple minded approach; All Pixelink monochrome cameras support PxLApi.PixelFormat.MONO8, and all
    # Pixelink color cameas support PxLApi.PixelFormat.BAYER8. So, try setting each of these to see if it 
    # works.
    
    # However, we should take care to restore the current pixel format.
    savedPixelFormat = 0
    newPixelFormat = 0
    ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.PIXEL_FORMAT)
    if not PxLApi.apiSuccess(ret[0]):
        return pixelType

    params = ret[2]
    savedPixelFormat = int(params[0])

    # Is it mono?
    newPixelFormat = PxLApi.PixelFormat.MONO8
    params = [newPixelFormat,]
    ret = PxLApi.setFeature(hCamera, PxLApi.FeatureId.PIXEL_FORMAT, PxLApi.FeatureFlags.MANUAL, params)
    if not PxLApi.apiSuccess(ret[0]):
        # Nope, so is it color?
        newPixelFormat = PxLApi.PixelFormat.BAYER8
        params = [newPixelFormat,]
        ret = PxLApi.setFeature(hCamera, PxLApi.FeatureId.PIXEL_FORMAT, PxLApi.FeatureFlags.MANUAL, params)
        if PxLApi.apiSuccess(ret[0]):
            # Yes, it IS color
            pixelType = PT_COLOR
    else:
        # Yes, it IS mono
        pixelType = PT_MONO

    # Restore the saved pixel format
    params = [savedPixelFormat,]
    PxLApi.setFeature(hCamera, PxLApi.FeatureId.PIXEL_FORMAT, PxLApi.FeatureFlags.MANUAL, params)

    return pixelType


def main():
    # Step 1 
    # Prepare the camera

    # Initialize any camera
    ret = PxLApi.initialize(0)
    if not PxLApi.apiSuccess(ret[0]):
        print("Error: Unable to initialize a camera")
        return EXIT_FAILURE
    hCamera = ret[1]

    # Step 2
    # Figure out if this is a mono or color camera, so that we know the type of
    # image we will be working with.
    pixelType = getPixelType(hCamera)
    if PT_OTHERWISE == pixelType:
        print("Error: We can't deal with this type of camera")
        PxLApi.uninitialize(hCamera)
        return EXIT_FAILURE

    # Just going to declare a very large buffer here
    # One that's large enough for any PixeLINK 4.0 camera
    rawFrame = create_string_buffer(5000 * 5000 * 2)

    # Step 3
    # Start the stream and Grab an image from the camera.
    ret = PxLApi.setStreamState(hCamera, PxLApi.StreamState.START)
    if not PxLApi.apiSuccess(ret[0]):
        print("Error: Unable to start the stream on the camera")
        PxLApi.uninitialize(hCamera)
        return EXIT_FAILURE

    ret = PxLApi.getNextFrame(hCamera, rawFrame)
    frameDesc = ret[1]
    if PxLApi.apiSuccess(ret[0]):
        # Convert it to a formatedImage. Note that frame can be in any one of a large number of pixel
        # formats, so we will simplify things by converting all mono to mono8, and all color to rgb24
        if PT_MONO == pixelType:
            ret = PxLApi.formatImage(rawFrame, frameDesc, PxLApi.ImageFormat.RAW_MONO8)
        else:
            ret = PxLApi.formatImage(rawFrame, frameDesc, PxLApi.ImageFormat.RAW_RGB24)
        if PxLApi.apiSuccess(ret[0]):
            formatedImage = ret[1]
            
            # Step 4
            # 'convert' the formatedImage buffer to a numpy ndarray that OpenCV can manipulate
            npFormatedImage = numpy.full_like(formatedImage, formatedImage, order="C") # a numpy ndarray
            npFormatedImage.dtype = numpy.uint8
            # Reshape the numpy ndarray into multidimensional array
            imageHeight = int(frameDesc.Roi.fHeight)
            imageWidth = int(frameDesc.Roi.fWidth)
            # color has 3 channels, mono just 1
            if PT_MONO == pixelType:
                newShape = (imageHeight, imageWidth)
            else:
                newShape = (imageHeight, imageWidth, 3)
            npFormatedImage = numpy.reshape(npFormatedImage, newShape)

            # Step 5
            # Do OpenCV manipulations on the numpy ndarray here.
            # We will simply use OpenCV to save the image as a BMP
            # Create a folder to save snapshots if it does not exist 
            if not os.path.exists("openCVSnapshot"):
                os.makedirs("openCVSnapshot")

            filepass = "openCVSnapshot/" + "snapshot.bmp"
            retVal = cv2.imwrite(filepass, npFormatedImage)
            if retVal:
                print("Saved image to 'openCVSnapshot/snapshot.bmp'")
            else:
                print("Error: Could not save image to 'openCVSnapshot/snapshot.bmp'")
    else:
        print("Error: Could not grab an image from the camera")

    # Step 6
    # Cleanup
    ret = PxLApi.setStreamState(hCamera, PxLApi.StreamState.STOP)
    assert PxLApi.apiSuccess(ret[0])
    ret = PxLApi.uninitialize(hCamera)
    assert PxLApi.apiSuccess(ret[0])
    
    return EXIT_SUCCESS


if __name__ == "__main__":
    main()
