"""
measureCallbackRate.py

Sample code to show how to create a simple callback. This program simply
calculates the frame rate of the camera (via callbacks).
"""

from pixelinkWrapper import*
from select import select
import sys
import time
import tty
import termios


@PxLApi._dataProcessFunction
def simple_callback(hCamera, frameData, dataFormat, frameDesc, userData):

    global gCallbackCount
    gCallbackCount += 1
    
    return 0


def main():

    sys.stdin.flush()

    ret = PxLApi.initialize(0)
    if not(PxLApi.apiSuccess(ret[0])):
        print("Could not initialize the camera! rc = %i" % ret[0])
        return 1

    hCamera = ret[1]

    ret = PxLApi.setCallback(hCamera, PxLApi.Callback.FRAME, None, simple_callback)
    if PxLApi.apiSuccess(ret[0]):
        ret = PxLApi.setStreamState(hCamera,PxLApi.StreamState.START)
        if PxLApi.apiSuccess(ret[0]):
            
            print("Counting the number of images over a 20 second period...")

            time.sleep(20) # Delay 20 seconds
            callbackCount = gCallbackCount

            PxLApi.setStreamState(hCamera,PxLApi.StreamState.STOP)
            PxLApi.setCallback(hCamera, PxLApi.Callback.FRAME, None, None) # Remove the callback
            print("    Received %i frames, or %8.2f frames/second" % (callbackCount, (float)(callbackCount/20.0)))
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
    gCallbackCount = 0 # Careful -- this global is not protected by a mutex
    main()