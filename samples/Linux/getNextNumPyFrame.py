"""
getNextFrame.py

A demonstration of a robust wrapper around PxLApi.getNextFrame.
"""

from pixelinkWrapper import*
from ctypes import*
import time
import numpy as np

# Just to define our image buffer;  One that's large enough for the Pixelink camera being used
MAX_WIDTH = 5000   # in pixels
MAX_HEIGHT = 5000  # in pixels
MAX_BYTES_PER_PIXEL = 3

"""
A robust wrapper around PxLApi.getNextFrame.
This will handle the occasional error that can be returned by the API because of timeouts. 

Note that this should only be called when grabbing images from a camera NOT currently configured for triggering. 
"""
def get_next_frame(hCamera, frame, maxNumberOfTries):

    ret = (PxLApi.ReturnCode.ApiUnknownError,)

    for i in range(maxNumberOfTries):
        ret = PxLApi.getNextNumPyFrame(hCamera, frame)
        if PxLApi.apiSuccess(ret[0]):
            return ret
        else:
            # If the streaming is turned off, or worse yet -- is gone?
            # If so, no sense in continuing.
            if PxLApi.ReturnCode.ApiStreamStopped == ret[0] or \
                PxLApi.ReturnCode.ApiNoCameraAvailableError == ret[0]:
                return ret
            else:
                print("    Hmmm... getNextFrame returned %i" % ret[0])

    # Ran out of tries, so return whatever the last error was.
    return ret


def main():

    firstFrame = True
    firstFrameTime = 0.0

    # Just going to declare a very large (NumPy 2D array)buffer here.
    frame = np.zeros([MAX_HEIGHT,MAX_WIDTH*MAX_BYTES_PER_PIXEL], dtype=np.uint8)

    # Initialize any camera
    ret = PxLApi.initialize(0)
    if not(PxLApi.apiSuccess(ret[0])):
        print("Error: Unable to initialize a camera! rc = %i" % ret[0])
        return 1

    hCamera = ret[1]

    # Start the stream
    ret = PxLApi.setStreamState(hCamera, PxLApi.StreamState.START)

    if PxLApi.apiSuccess(ret[0]):
        for i in range(15):            
            ret = get_next_frame(hCamera, frame, 5)
            print("\ngetNextFrame returned %i" % ret[0])
            if PxLApi.apiSuccess(ret[0]):
                frameDescriptor = ret[1]
                if firstFrame:
                    firstFrameTime = frameDescriptor.fFrameTime
                    firstFrame = False
                print("\tframe number %i, frame time %3.3f" % (frameDescriptor.uFrameNumber, frameDescriptor.fFrameTime - firstFrameTime))
            else:
                if PxLApi.ReturnCode.ApiBufferTooSmall == ret[0]:
                    print("This program can only capture frames of %i bytes, or smaller. Reduce the camera's ROI" % frame.size)   
            time.sleep(0.5) # 500 ms
    else:
        print("setStreamState with StreamState.START failed, rc = %i" % ret[0])

    PxLApi.setStreamState(hCamera, PxLApi.StreamState.STOP)
    assert PxLApi.apiSuccess(ret[0]), "setStreamState with StreamState.STOP failed"

    PxLApi.uninitialize(hCamera)
    assert PxLApi.apiSuccess(ret[0]), "uninitialize failed"
    
    return 0


if __name__ == "__main__":
    main()
