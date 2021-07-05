"""
setPreviewSettings.py

A simple application that previews the camera, and demonstrates how to make adjustments 
to that window, as well as some camera settings that affect the camera's preview.
"""

from pixelinkWrapper import*
from ctypes import*
import ctypes.wintypes
import time
import threading

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
    assert PxLApi.apiSuccess(ret[0]), "%i" % ret[0]

"""
Creates a new preview thread for each preview run
"""
def create_new_preview_thread(hCamera):
    # Creates a thread with preview control based on the setPreviewState function
    return threading.Thread(target=control_preview_thread, args=(hCamera,), daemon=True)

"""
Certain camera operations cannot be done while the camera is streaming
This function is written to temporarily stop the video stream.
"""
def interrupt_stream_state(hCamera, interrupt):
    # Controls preview thread
    global previewState
    if interrupt:
        # Interrupt stream
        previewState = PxLApi.PreviewState.STOP
        time.sleep(0.1) # delay of 0.1 second allows stopping the preview before interrupting stream
        ret = PxLApi.setStreamState(hCamera, PxLApi.StreamState.STOP)
        assert PxLApi.apiSuccess(ret[0])
    else:
        # Recover stream
        ret = PxLApi.setStreamState(hCamera, PxLApi.StreamState.START)
        assert PxLApi.apiSuccess(ret[0])        
        # Declare control preview thread that can control preview and poll the message pump on Windows
        previewThread = create_new_preview_thread(hCamera)
        # Run preview
        previewState = PxLApi.PreviewState.START
        previewThread.start()


def main():
    global previewState
    colorCamera = True
    
    # Step 0
    # Grab the first camera we find
    ret = PxLApi.initialize(0)
    if PxLApi.apiSuccess(ret[0]):
        hCamera = ret[1]

        # Step 1
        # Preview at a set ROI of 800 x 600

        # Set the ROI to a fixed size of 800x600
        roi = [0, 0, 800, 600]
        ret = PxLApi.setFeature(hCamera, PxLApi.FeatureId.ROI, PxLApi.FeatureFlags.MANUAL, roi)
        assert PxLApi.apiSuccess(ret[0])

        # Just use all of the other camera's default settings.
		# Start the stream
        ret = PxLApi.setStreamState(hCamera, PxLApi.StreamState.START)
        assert PxLApi.apiSuccess(ret[0])

        print("Previewing 800 x 600...")

        # Start the preview (NOTE: camera must be streaming)
        # Declare control preview thread that can control preview and poll the message pump on Windows
        previewThread = create_new_preview_thread(hCamera)
        # Run preview
        previewState = PxLApi.PreviewState.START
        previewThread.start()

        time.sleep(5) # delay 5 seconds

        # Step 2
        # Change the preview window to 1024 x 768

        print("Scaling preview up to 1024 x 768...")

        ret = PxLApi.setPreviewSettings(hCamera, "1024 x 768 preview window", width=1024, height=768)
        assert PxLApi.apiSuccess(ret[0])

        time.sleep(5) # delay 5 seconds

        # Step 3
        # Change to the ROI to 640 x 480

        print("Changing ROI to 640 x 480, preview window size is the same, but the image is zoomed in...")

        # The ROI cannot be changed while streaming, so interrupt the stream for the adjustment
        interrupt_stream_state(hCamera, True)

        roi = [0, 0, 640, 480]
        ret = PxLApi.setFeature(hCamera, PxLApi.FeatureId.ROI, PxLApi.FeatureFlags.MANUAL, roi)
        assert PxLApi.apiSuccess(ret[0])

        interrupt_stream_state(hCamera, False)
        time.sleep(5) # delay 5 seconds

        # Step 4
        # Change to the ROI to 1280 x 1024

        print("Changing ROI to 1280 x 1024, preview window size is the same, but the image is zoomed out...")

        # The ROI cannot be changed while streaming, so interrupt the stream for the adjustment
        interrupt_stream_state(hCamera, True)

        roi = [0, 0, 1280, 1024]
        ret = PxLApi.setFeature(hCamera, PxLApi.FeatureId.ROI, PxLApi.FeatureFlags.MANUAL, roi)
        assert PxLApi.apiSuccess(ret[0])

        interrupt_stream_state(hCamera, False)
        time.sleep(5) # delay 5 seconds

        # Step 5
        # Change to YUV format (if supported)

        print("Changing pixel format to YUV...")

        # The pixel format cannot be changed while streaming, so interrupt the stream for the adjustment
        interrupt_stream_state(hCamera, True)

        pixelFormat = [PxLApi.PixelFormat.YUV422, ]
        ret = PxLApi.setFeature(hCamera, PxLApi.FeatureId.PIXEL_FORMAT, PxLApi.FeatureFlags.MANUAL, pixelFormat)
        if not PxLApi.apiSuccess(ret[0]):
            print("Changing pixel format to YUV returned %i" % ret[0])
            colorCamera = False

        interrupt_stream_state(hCamera, False)
        time.sleep(5) # delay 5 seconds

        # Step 6
        # Change to 16bit format

        print("Changing pixel format to 16 bit...")

        # The pixel format cannot be changed while streaming, so interrupt the stream for the adjustment
        interrupt_stream_state(hCamera, True)

        if colorCamera:
            pixelFormat[0] = PxLApi.PixelFormat.BAYER16
        else:
            pixelFormat[0] = PxLApi.PixelFormat.MONO16
        ret = PxLApi.setFeature(hCamera, PxLApi.FeatureId.PIXEL_FORMAT, PxLApi.FeatureFlags.MANUAL, pixelFormat)
        assert PxLApi.apiSuccess(ret[0])

        interrupt_stream_state(hCamera, False)
        time.sleep(5) # delay 5 seconds

        # Step 7
        # Change the window size to match the ROI

        print("Changing preview window size to match the ROI (1280 x 1024)...")

        ret = PxLApi.resetPreviewWindow(hCamera)
        assert PxLApi.apiSuccess(ret[0])

        time.sleep(5) # delay 5 seconds

        # Step 8
        # Change back to simple 8bit format

        print("Changing pixel format to 8 bit...")

        # The pixel format cannot be changed while streaming, so interrupt the stream for the adjustment
        interrupt_stream_state(hCamera, True)

        if colorCamera:
            pixelFormat[0] = PxLApi.PixelFormat.BAYER8
        else:
            pixelFormat[0] = PxLApi.PixelFormat.MONO8
        ret = PxLApi.setFeature(hCamera, PxLApi.FeatureId.PIXEL_FORMAT, PxLApi.FeatureFlags.MANUAL, pixelFormat)
        assert PxLApi.apiSuccess(ret[0])

        interrupt_stream_state(hCamera, False)
        time.sleep(5) # delay 5 seconds

        # Step 9
        # Vertically flip the image

        print("Vertically flipping the image...")

        # The PxLApi.FeatureId.FLIP cannot be changed while streaming, so interrupt the stream for the adjustment
        interrupt_stream_state(hCamera, True)

        flip = [0, 1]
        ret = PxLApi.setFeature(hCamera, PxLApi.FeatureId.FLIP, PxLApi.FeatureFlags.MANUAL, flip)
        assert PxLApi.apiSuccess(ret[0])

        interrupt_stream_state(hCamera, False)
        time.sleep(5) # delay 5 seconds

        # Step 10
        # Rotate the image 270 degrees

        print("Rotating the image...")

        # The PxLApi.FeatureId.ROTATE cannot be changed while streaming, so interrupt the stream for the adjustment
        interrupt_stream_state(hCamera, True)

        rotate = [270, ]
        ret = PxLApi.setFeature(hCamera, PxLApi.FeatureId.ROTATE, PxLApi.FeatureFlags.MANUAL, rotate)
        assert PxLApi.apiSuccess(ret[0])

        interrupt_stream_state(hCamera, False)
        time.sleep(5) # delay 5 seconds
        
        # Step 11
        # Done. Just tidy up.

        # Stop the preview
        previewState = PxLApi.PreviewState.STOP
        time.sleep(0.1) # delay of 0.1 second allows stopping the preview before interrupting stream

        # Stop the stream        
        ret = PxLApi.setStreamState(hCamera, PxLApi.StreamState.STOP)
        assert PxLApi.apiSuccess(ret[0])

        # Uninitialize the camera now that we're done with it.
        PxLApi.uninitialize(hCamera)

    return 0


if __name__ == "__main__":
    previewState = PxLApi.PreviewState.STOP # control preview thread
    main()