"""
preview.py

A simple application that previews the camera.
"""

from pixelinkWrapper import*
from ctypes import*
import ctypes.wintypes
import time
import threading
import msvcrt

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
Preview control thread function based on the setPreviewStateEx function
"""
def control_preview_thread_with_callback(hCamera):
    
    context = None
    # The preview window will go 'Not Responding' if we do not poll the message pump, and 
    # forward events onto it's handler on Windows.
    user32 = windll.user32
    msg = ctypes.wintypes.MSG()
    pMsg = ctypes.byref(msg)

    # Start the preview (NOTE: camera must be streaming)
    ret = PxLApi.setPreviewStateEx(hCamera, PxLApi.PreviewState.START, context, changeFunction)
    
    while (PxLApi.PreviewState.START == previewState and PxLApi.apiSuccess(ret[0])):
        if user32.PeekMessageW(pMsg, 0, 0, 0, 1) != 0:            
            user32.TranslateMessage(pMsg)
            user32.DispatchMessageW(pMsg)
    
    # Stop the preview
    ret = PxLApi.setPreviewStateEx(hCamera, PxLApi.PreviewState.STOP, context, changeFunction)
    assert PxLApi.apiSuccess(ret[0]), "%i" % ret[0]

"""
Creates a new preview thread for each preview run
"""
def create_new_preview_thread(hCamera, withCallback):
    if withCallback:
        # Creates a thread with preview control based on the setPreviewStateEx function
        return threading.Thread(target=control_preview_thread_with_callback, args=(hCamera,), daemon=True)

    # Creates a thread with preview control based on the setPreviewState function
    return threading.Thread(target=control_preview_thread, args=(hCamera,), daemon=True)

"""
Start and stop preview.
Preview gets stopped after a user presses a key.
"""
def set_preview_state(hCamera):
    # Controls preview thread
    global previewState

    # Declare control preview thread that can control preview and poll the message pump on Windows
    previewThread = create_new_preview_thread(hCamera, False)
    
    # Run preview until the user presses a key....
    previewState = PxLApi.PreviewState.START
    previewThread.start()
    print("Press any key to stop preview......")
    kbHit()
    previewState = PxLApi.PreviewState.STOP
    # Give preview time to stop
    time.sleep(0.05)

"""
Start and stop preview using setPreviewStateEx with a callback function.
Preview gets stopped after a user presses a key
"""
def set_preview_state_ex(hCamera):
    # Controls preview thread
    global previewState
    
    # Declare control preview thread that can control preview and poll the message pump on Windows
    previewThread = create_new_preview_thread(hCamera, True)

    # Run the preview until the user presses a key....
    previewState = PxLApi.PreviewState.START
    previewThread.start()
    print("Press any key to stop preview with callback and exit.......")
    kbHit()
    previewState = PxLApi.PreviewState.STOP
    # Give preview time to stop
    time.sleep(0.05)


def main():

    # Grab the first camera we find
    ret = PxLApi.initialize(0)
    if PxLApi.apiSuccess(ret[0]):
        hCamera = ret[1]
                
        # Just use all of the camer's default settings.
        # Start the stream
        ret = PxLApi.setStreamState(hCamera, PxLApi.StreamState.START)
        assert PxLApi.apiSuccess(ret[0]), "%i" % ret[0]

        # Start and stop preview using setPreviewState
        set_preview_state(hCamera)
    
        # Run the preview until the user presses a key....
        print("Press any key to start preview with callback......")
        kbHit()

        # Start and stop preview using setPreviewStateEx
        set_preview_state_ex(hCamera)

        # Stop the stream
        ret = PxLApi.setStreamState(hCamera, PxLApi.StreamState.STOP)
        assert PxLApi.apiSuccess(ret[0]), "%i" % ret[0]

        # Uninitialize the camera now that we're done with it.
        PxLApi.uninitialize(hCamera)

    return 0

"""
Unbuffered keyboard input on command line.
Keyboard input will be passed to the application without the user pressing
the enter key.
Note: IDLE does not support this functionality.
"""
def kbHit():
    return msvcrt.getch()

"""
Callback function for setPreviewStateEx
"""
@PxLApi._changeFunction
def changeFunction(hCamera, changeCode, context):
    print("Callback function executed with changeCode = %i  " % changeCode)
    return 0


if __name__ == "__main__":
    previewState = PxLApi.PreviewState.STOP # control preview thread
    main()
