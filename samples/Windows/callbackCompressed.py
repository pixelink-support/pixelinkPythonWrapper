"""
callbackCompressed.py

Sample code shows how to receive, via callback, both compressed and decompressed
images from a camera that has compression enabled.
"""

from pixelinkWrapper import*
from ctypes import*
import ctypes.wintypes
import time
import threading

A_OK = 0
GENERAL_ERROR = 1

ON = 1
OFF = 0

"""
Checks if a BAYER8 pixel format is being used by the specified camera.
"""
def is_bayer8(pixelFormat):
    if pixelFormat == PxLApi.PixelFormat.BAYER8_RGGB or \
       pixelFormat == PxLApi.PixelFormat.BAYER8_GBRG or \
       pixelFormat == PxLApi.PixelFormat.BAYER8_BGGR or \
       pixelFormat == PxLApi.PixelFormat.BAYER8_GRBG:
        return True

    return False

"""
This PxLApi.Callback.FRAME callback function will be called when a decompressed image is available from the camera.
"""
@PxLApi._dataProcessFunction
def frame_callback_function(hCamera, frameData, dataFormat, frameDesc, userData):
    # This function should only ever receive uncompressed frames    
    frameDescriptor = frameDesc.contents
    assert frameDescriptor.CompressionInfo.fCompressionStrategy == PxLApi.CompressionStrategy.NONE

    print("     Uncompressed -- FrameSize:{0} FrameData(hex):{1:02X}{2:02X}{3:02X}{4:02X} {5:02X}{6:02X}{7:02X}{8:02X} "
          "{9:02X}{10:02X}{11:02X}{12:02X} {13:02X}{14:02X}{15:02X}{16:02X}".format(int(frameDescriptor.CompressionInfo.fCompressedSize), 
                                                   frameData[3], frameData[2], frameData[1], frameData[0], 
                                                   frameData[7], frameData[6], frameData[5], frameData[4], 
                                                   frameData[11], frameData[10], frameData[9], frameData[8],
                                                   frameData[15], frameData[14], frameData[13], frameData[12]))

    return PxLApi.ReturnCode.ApiSuccess

"""
This PxLApi.Callback.COMPRESSED_FRAME callback function will be called when a compressed image is available from the camera.
"""
@PxLApi._dataProcessFunction
def pixelink10_frame_callback_function(hCamera, frameData, dataFormat, frameDesc, userData):
    # This function should only ever receive Pixelink10 compressed frames
    frameDescriptor = frameDesc.contents
    assert frameDescriptor.CompressionInfo.fCompressionStrategy == PxLApi.CompressionStrategy.PIXELINK10

    print("     Compressed -- FrameSize:{0} FrameData(hex):{1:02X}{2:02X}{3:02X}{4:02X} {5:02X}{6:02X}{7:02X}{8:02X} "
          "{9:02X}{10:02X}{11:02X}{12:02X} {13:02X}{14:02X}{15:02X}{16:02X}".format(int(frameDescriptor.CompressionInfo.fCompressedSize), 
                                                   frameData[3], frameData[2], frameData[1], frameData[0], 
                                                   frameData[7], frameData[6], frameData[5], frameData[4], 
                                                   frameData[11], frameData[10], frameData[9], frameData[8],
                                                   frameData[15], frameData[14], frameData[13], frameData[12]))

    return PxLApi.ReturnCode.ApiSuccess

"""
Returns the frame size of the specified camera using the current camera settings.
"""
def get_frame_size(hCamera, bytesPerPixel):

    # Determine the ROI size
    ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.ROI)
    if not PxLApi.apiSuccess(ret[0]):
        return ret
    params = ret[2]
    width = params[PxLApi.RoiParams.WIDTH]
    height = params[PxLApi.RoiParams.HEIGHT]

    # Determine if there is any pixel addressing applied
    ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.PIXEL_ADDRESSING)
    if not PxLApi.apiSuccess(ret[0]):
        return ret
    params = ret[2]
    paX = params[PxLApi.PixelAddressingParams.X_VALUE]
    paY = params[PxLApi.PixelAddressingParams.Y_VALUE]
    width = width / paX
    height = height / paY

    # Determine if HDR Interleaved is applied
    hdrInterleaveMultiplier = 1

    ret2 = PxLApi.getFeature(hCamera, PxLApi.FeatureId.GAIN_HDR)
    if PxLApi.apiSuccess(ret2[0]):
        params = ret2[2]
        if int(params[0]) == PxLApi.GainHdr.INTERLEAVED:
            hdrInterleaveMultiplier = 2

    width = width * hdrInterleaveMultiplier

    return int(width * height * bytesPerPixel)

"""
Preview control thread function based on the setPreviewState function
"""
def control_preview_thread(hCamera):
    
    # The preview window will go 'Not Responding' if we do not poll the message pump, and 
    # forward events onto it's handler on Windows.
    user32 = windll.user32
    msg = ctypes.wintypes.MSG()
    pMsg = ctypes.byref(msg)

    # Start the preview (NOTE: camera must be streaming)
    ret = PxLApi.setPreviewState(hCamera, PxLApi.PreviewState.START)
    
    while (PxLApi.PreviewState.START == previewState and PxLApi.apiSuccess(ret[0])):
        if user32.PeekMessageW(pMsg, 0, 0, 0, 1) != 0:            
            user32.TranslateMessage(pMsg)
            user32.DispatchMessageW(pMsg)
    
    # Stop the preview
    ret = PxLApi.setPreviewState(hCamera, PxLApi.PreviewState.STOP)

"""
Creates a new preview thread for each preview run
"""
def create_new_preview_thread(hCamera):
    # Creates a thread with preview control based on the setPreviewState function
    return threading.Thread(target=control_preview_thread, args=(hCamera,), daemon=True)

"""
Start and stop preview
"""
def preview(hCamera, on):
    # Controls preview thread
    global previewState

    if on:
        # Change preview settings
        PxLApi.setPreviewSettings(hCamera, width=800, height=600)
        # Declare control preview thread that can control preview and poll the message pump on Windows
        previewThread = create_new_preview_thread(hCamera)
        # Run preview
        previewState = PxLApi.PreviewState.START
        previewThread.start()
    else:
        previewState = PxLApi.PreviewState.STOP


def main():

    # Step 1
	# Grab a camera
    ret = PxLApi.initialize(0)
    if not PxLApi.apiSuccess(ret[0]):
        print("  Could not find a camera.  rc = {0}".format(ret[0]))
        return GENERAL_ERROR
    hCamera = ret[1]

    # Step 2
    # Make sure the camera is configured correctly:
    #  - Pixel format is either MONO8 or BAYER8
    # And then determine the frame size
    pixelFormat = [PxLApi.PixelFormat.MONO8,]
    ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.PIXEL_FORMAT)
    if not PxLApi.apiSuccess(ret[0]):
        print("  Unable to get pixel format.  rc = {0}".format(ret[0]))
        PxLApi.uninitialize(hCamera)
        return GENERAL_ERROR
    
    params = ret[2]
    pixelFormat = int(params[0])
    if not pixelFormat == PxLApi.PixelFormat.MONO8 and not is_bayer8(pixelFormat):
        print("  Unknown pixel format.  format = {0}".format(pixelFormat))
        PxLApi.uninitialize(hCamera)
        return GENERAL_ERROR

    frameSize = get_frame_size(hCamera, PxLApi.getBytesPerPixel(pixelFormat))
    if isinstance(frameSize, tuple):
        ret = frameSize
        print("  Unknown frame size.  rc = {0}".format(ret[0]))
        PxLApi.uninitialize(hCamera)
        return GENERAL_ERROR

    # Step 3
    # Enable compression
    params = [pixelFormat, PxLApi.CompressionStrategy.PIXELINK10]
    ret = PxLApi.setFeature(hCamera, PxLApi.FeatureId.COMPRESSION, PxLApi.FeatureFlags.MANUAL, params)
    if not PxLApi.apiSuccess(ret[0]):
        print("  Cannot enable compression.  Are you sure this camera supports it?  rc = {0}".format(ret[0]))
        PxLApi.uninitialize(hCamera)
        return GENERAL_ERROR

    # Step 4
    # Enable both the PxLApi.Callback.FRAME and PxLApi.Callback.COMPRESSED_FRAME type callbacks. This may look a 
    # little unusual, but that tells the API:
    # - If the stream is not compressed, then return the uncompressed frames via FrameCallbackFunction. However,
    # - If the stream is compressed, then return the compressed frames via pixelink10_frame_callback_function
    ret = PxLApi.setCallback(hCamera, PxLApi.Callback.FRAME, None, frame_callback_function)
    if not PxLApi.apiSuccess(ret[0]):
        print("  Error: Could not set the frame callback")
        PxLApi.uninitialize(hCamera)
        return GENERAL_ERROR

    # Be sure to set the compression strategy, so that the Pixelink API knows what type of compression this callback is for.
    context = PxLApi.CompressionInfoPixelink10()
    context.uCompressionStrategy = PxLApi.CompressionStrategy.PIXELINK10
    ret = PxLApi.setCallback(hCamera, PxLApi.Callback.COMPRESSED_FRAME, context, pixelink10_frame_callback_function)
    print(ret[0])
    if not PxLApi.apiSuccess(ret[0]):
        print("  Error: Could not set the compressed frame callback")
        PxLApi.uninitialize(hCamera)
        return GENERAL_ERROR

    # Step 5
    # Enable the stream, with preview, for 3 seconds.
    # Under these circumstances, each frame received from the camera will be decompressed (required for the preview) -- but
    # the preview will show the decompressed variant, while the callback will receive the compressed variant.
    print("  Enabling the stream with preview for 3 seconds -- you should see compressed callbacks + uncompressed preview ...")
    ret = PxLApi.setStreamState(hCamera, PxLApi.StreamState.START)
    if not PxLApi.apiSuccess(ret[0]):
        print("  Cannot start the stream.  rc = {0}".format(ret[0]))
        PxLApi.uninitialize(hCamera)
        return GENERAL_ERROR

    preview(hCamera, ON)
    time.sleep(3)
    preview(hCamera, OFF)
    PxLApi.setStreamState(hCamera, PxLApi.StreamState.STOP)

    # Step 6
    # Enable the stream, without preview, for 3 seconds.
    # Under these circumstances, each frame received from the camera will not be decompressed; the compressed
    # frame will simply be returned via the callback.
    print("  Enabling the stream without preview for 3 seconds -- you should see compressed callbacks ...")
    ret = PxLApi.setStreamState(hCamera, PxLApi.StreamState.START)
    if not PxLApi.apiSuccess(ret[0]):
        print("  Cannot start the stream.  rc = {0}".format(ret[0]))
        PxLApi.uninitialize(hCamera)
        return GENERAL_ERROR

    time.sleep(3)
    PxLApi.setStreamState(hCamera, PxLApi.StreamState.STOP)

    # Step 7
    # Cancel the callback for the compressed frames
    ret = PxLApi.setCallback(hCamera, PxLApi.Callback.COMPRESSED_FRAME, context, 0)
    if not PxLApi.apiSuccess(ret[0]):
        print("  Error: Could not cancel the compressed frame callback")
        PxLApi.uninitialize(hCamera)
        return GENERAL_ERROR

    # Step 8
    # Enable the stream for 3 seconds.
    print("  Enabling the stream for 3 seconds -- you should see uncompressed callbacks...")
    ret = PxLApi.setStreamState(hCamera, PxLApi.StreamState.START)
    if not PxLApi.apiSuccess(ret[0]):
        print("  Cannot start the stream.  rc = {0}".format(ret[0]))
        PxLApi.uninitialize(hCamera)
        return GENERAL_ERROR

    time.sleep(3)
    PxLApi.setStreamState(hCamera, PxLApi.StreamState.STOP)

    # Step 9
    # Cleanup
    PxLApi.uninitialize(hCamera)

    return A_OK


if __name__ == "__main__":
    previewState = PxLApi.PreviewState.STOP # control preview thread
    main()
