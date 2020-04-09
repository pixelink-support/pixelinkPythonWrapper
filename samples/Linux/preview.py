"""
preview.py

A simple application that previews the camera.
"""

from pixelinkWrapper import*
import sys
import tty
import termios

"""
Start and stop preview.
Preview gets stopped after a user presses a key.
"""
def set_preview_state(hCamera):
    
    # Start the preview (NOTE: camera must be streaming)
    ret = PxLApi.setPreviewState(hCamera, PxLApi.PreviewState.START)
    assert PxLApi.apiSuccess(ret[0]), "%i" % ret[0]

    # Run preview until the user presses a key....
    print("Press any key to stop preview......")
    kbHit()

    # Stop the preview
    ret = PxLApi.setPreviewState(hCamera, PxLApi.PreviewState.STOP)
    assert PxLApi.apiSuccess(ret[0]), "%i" % ret[0]

"""
Start and stop preview using setPreviewStateEx with a callback function.
Preview gets stopped after a user presses a key
"""
def set_preview_state_ex(hCamera):
    
    context = None
    # Start the preview
    ret = PxLApi.setPreviewStateEx(hCamera, PxLApi.PreviewState.START, context, changeFunction)
    assert PxLApi.apiSuccess(ret[0]), "%i" % ret[0]

    # Run the preview until the user presses a key....
    print("Press any key to stop preview with callback and exit......")
    kbHit()

    # Stop the preview
    ret = PxLApi.setPreviewStateEx(hCamera, PxLApi.PreviewState.START, context, changeFunction)
    assert PxLApi.apiSuccess(ret[0]), "%i" % ret[0]


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

        # Run preview with callback when the user presses a key
        print("Press any key to start preview with callback......")
        kbHit()
        # Start and stop preview using setPreviewStateEx
        set_preview_state_ex(hCamera)
        print("\r")

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
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

"""
Callback function for setPreviewStateEx
"""
@PxLApi._changeFunction
def changeFunction(hCamera, changeCode, context):
    print("\rCallback executed with changeCode = %i  " % changeCode, end="")
    return 0


if __name__ == "__main__":
    main()
