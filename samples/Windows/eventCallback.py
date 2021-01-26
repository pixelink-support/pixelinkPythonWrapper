"""
eventCallback.py 

Demonstrates how to use event callbacks
"""

from pixelinkWrapper import*
import time
import msvcrt

STALL_TIME = 20     # 20 seconds
EXIT_SUCCESS = 0
EXIT_FAILURE = 1

"""
Callback function called by the API with each event (of interest) reported by the camera. 
N.B. This is called by the API on a thread created in the API.
"""
@PxLApi._eventProcessFunction
def event_callback_func(
    hCamera,            \
    eventId,            \
    eventTimestamp,     \
    numDataBytes,       \
    data,               \
    userData):

    # Copy event specific data, if it is provided
    eventData = data.contents if bool(data) == True else 0

    print("EventCallbackFunction: hCamera=%s, eventId=%d" % (hex(hCamera), eventId))
    print("     eventTimestamp=%f, numDataBytes=%d" % (eventTimestamp, numDataBytes))
    print("     eventData=%s, userData=%d (%s)\n" % (hex(eventData), userData, hex(userData)))
    return PxLApi.ReturnCode.ApiSuccess


def main():

    print("This sample application will use the GPI line to demostrate events, OK to proceed Y/N?")
    userChar = kbHit()
    if 'y' != userChar and 'Y' != userChar:
        return EXIT_SUCCESS

    ret = PxLApi.initialize(0)
    if not PxLApi.apiSuccess(ret[0]):
        print("ERROR on PxLApi.initialize: %d" % ret[0])
        return EXIT_FAILURE

    hCamera = ret[1]

    print("\nMain thread, stalling for %d seconds awaiting events.  Toggle the GPI line...\n" % STALL_TIME)

    userData = 1526647550   # hex(0x5AFECAFE)
    # Note: We can specify a specific event, or all of them
    ret = PxLApi.setEventCallback(
        hCamera,                \
        PxLApi.EventId.ANY,     \
        userData,               \
        event_callback_func)

    if not PxLApi.apiSuccess(ret[0]):
        retErr = PxLApi.getErrorReport(hCamera)
        err = retErr[1]
        print("ERROR setting event callback function: %d (%s)" % (ret[0], str(err.strReturnCode, encoding='utf-8')))
        PxLApi.uninitialize(hCamera)
        return EXIT_FAILURE

    time.sleep(STALL_TIME)

    PxLApi.setEventCallback(hCamera, PxLApi.EventId.ANY, userData, 0)   # Cancel the callback
    PxLApi.uninitialize(hCamera)
    return EXIT_SUCCESS


"""
Unbuffered keyboard input on command line.
Keyboard input will be passed to the application without the user pressing
the enter key.
Note: IDLE does not support this functionality.
"""
def kbHit():
    keyPressed = msvcrt.getch()
    if b'\xe0' == keyPressed:
        return str(keyPressed)
    return str(keyPressed, "utf-8")


if __name__ == "__main__":
    main()
