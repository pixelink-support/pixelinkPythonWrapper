"""
measureGetNextFrameRate.py

Sample code to show a very simple frame grab. See the sample application
'getNextFrame' for a more robust frame grab example.

This program simply calculates the frame rate of the camera (via frame grabs).
"""

from pixelinkWrapper import*
from ctypes import*
from select import select
import sys
import time
import tty
import termios


def no_camera(rc):

    if rc == PxLApi.ReturnCode.ApiNoCameraError or rc == PxLApi.ReturnCode.ApiNoCameraAvailableError:
        return True

    return False


def main():

    getNextFramesPerItteration = 1

    # Just going to declare a very large buffer here
    # One that's large enough for any PixeLINK 4.0 camera
    frame = create_string_buffer(5000 * 5000 * 2)

    sys.stdin.flush()

    ret = PxLApi.initialize(0)
    if not(PxLApi.apiSuccess(ret[0])):
        print("Could not initialize the camera! rc = %i" % ret[0])
        return 1

    hCamera = ret[1]

    ret = PxLApi.setStreamState(hCamera, PxLApi.StreamState.START)
    if not(PxLApi.apiSuccess(ret[0])):
        print("Could not stream the camera! rc = %i" % ret[0])
        PxLApi.uninitialize(hCamera)
        return 1

    print("Counting the number of images over a 20 second period...")

    frameCount = badFrameCount = 0
    startTime = currentTime = time.time() * 1000.0 # in milliseconds

    while 1:
        
        for i in range(getNextFramesPerItteration):
            ret = PxLApi.getNextFrame(hCamera, frame)
            if PxLApi.apiSuccess(ret[0]):
                frameCount += 1
            else:
                badFrameCount += 1
                if no_camera(ret[0]):
                    print("Camera is Gone!! -- Aborting")
                    return 1 # No point is continuing
                break # Do a time check to see if we are done.

        currentTime = time.time() * 1000.0

        if currentTime >= (startTime + 20000):
            break
        if currentTime <= (startTime + 200):
            getNextFramesPerItteration = getNextFramesPerItteration << 1

    PxLApi.setStreamState(hCamera, PxLApi.StreamState.STOP)

    print("    Received %i frames (%i bad), or %8.2f frames/second.  %i getNextFrames/timecheck" %
          (frameCount+badFrameCount, badFrameCount, (frameCount+badFrameCount)/((currentTime - startTime) / 1000.0),
           getNextFramesPerItteration))

    print("Press any key to exit")
    setUnbufKb(True)
    kbHit()
    setUnbufKb(False)
    print("\r")

    PxLApi.uninitialize(hCamera)

    return 0

"""
Unbuffered keyboard input on command line.
Keyboard input will be passed to the application without the user pressing
the enter key.
Note: IDLE does not support this functionality.
"""
# A couple of useful global variables
fd = sys.stdin.fileno()
original_term_settings = termios.tcgetattr(fd)

# Enable/disable unbuffered keyboard input
def setUnbufKb(enable):
    if enable:
        tty.setraw(sys.stdin.fileno())
    else:
        termios.tcsetattr(fd, termios.TCSADRAIN, original_term_settings)

# Read hit button
def kbHit():
    return sys.stdin.read(1)


if __name__ == "__main__":
    main()
