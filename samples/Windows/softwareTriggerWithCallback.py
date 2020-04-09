"""
softwareTriggerWithCallback.py

A demonstration of a special software triggering mode.

With normal software triggering on Pixelink cameras, a call to PxLApi.getNextFrame will cause the API to:

1) notify the camera to take an image
2) wait until the image is returned.
3) return the image

If the camera were configured to have a 10 second exposure, the thread calling PxLApi.getNextFrame would be blocked
inside PxLApi.getNextFrame for the entire 10 seconds.

By using callbacks and calling PxLApi.getNextFrame in a special way, it's possible to emulate a hardware trigger. 
Calling PxLApi.getNextFrame with a None or 0 frame buffer:

1) notify the camera to take an image.

and that's it. How do you get the image? It will be handed to you in an PxLApi.Callback.FRAME callback. 

Using this technique, it's possible to sofware trigger multiple cameras reasonably simultaneously.
This technique is demonstrated here. 

This application will detect and connect to all PixeLINK 4.0 cameras, configure each for software triggering
(assuming all cameras support triggering), set them all streaming, and then software trigger them at 
regular intervals.
"""

from pixelinkWrapper import*
import threading
import time

SUCCESS = 0
FAILURE = 1


def prepare_camera_for_test(hCamera):

    ret = set_up_software_triggering(hCamera)
    if PxLApi.apiSuccess(ret[0]):
        # Set up PxLApi.Callback.FRAME callbacks for this camera
        ret = PxLApi.setCallback(hCamera, PxLApi.Callback.FRAME, 0, image_callback_function)
        if PxLApi.apiSuccess(ret[0]):
            return PxLApi.setStreamState(hCamera, PxLApi.StreamState.START)
    return ret

"""
Given a camera handle, configure the camera for software triggering.
"""
def set_up_software_triggering(hCamera):

    ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.TRIGGER)
    if PxLApi.apiSuccess(ret[0]):        
        assert len(ret[2]) >= PxLApi.TriggerParams.NUM_PARAMS

        flags = ret[1]
        params = ret[2]

        params[PxLApi.TriggerParams.MODE] = PxLApi.TriggerModes.MODE_0
        params[PxLApi.TriggerParams.TYPE] = PxLApi.TriggerTypes.SOFTWARE
        # Leave the rest of the params the way they are

        flags = enable_feature(flags, True) # enable triggering

        ret = PxLApi.setFeature(hCamera, PxLApi.FeatureId.TRIGGER, flags, params)

    return ret

"""
Sets flags to enable/disable a feature
"""
def enable_feature(flags, enable):
    if enable:
        flags = ~PxLApi.FeatureFlags.MOD_BITS | PxLApi.FeatureFlags.MANUAL
    else:
        flags = ~PxLApi.FeatureFlags.MOD_BITS | PxLApi.FeatureFlags.OFF
    return flags

"""
This PxLApi.Callback.FRAME callback function will be called when an image is available from the camera.

Note that frame time is relative to when the camera started streaming, so you have to make sure that 
the cameras start streaming at approximately the same time. If you're single-stepping through this code 
in a debugger, that's likely not the case.
"""
@PxLApi._dataProcessFunction
def image_callback_function(hCamera, frame, dataFormat, frameDesc, context):

    frameDescriptor = frameDesc.contents
    print("Callback on thread %s for camera %s, frameTime = %f" % (hex(id(threading.current_thread())), hex(hCamera), frameDescriptor.fFrameTime))
    return SUCCESS


def do_test(hCameras, numberOfCapturesToDo):
    
    # Cameras should be streaming now and ready.
    for numTimes in range(numberOfCapturesToDo):
        print("")
        # Fire a software trigger on all of the cameras as quickly as possible
        for i in range(len(hCameras)):

            # By passing in a None or 0 frame buffer, we're saying to a camera that is configured for software triggering
            # that we just want to quickly trigger the camera, and not wait for the image to be exposed and sent back to the host.
            # Just start taking the picture.
            # We'll receive the picture in the callback function we've registered.
            ret = PxLApi.getNextFrame(hCameras[i], None)
            if not PxLApi.apiSuccess(ret[0]):
                print("Error: PxLApi.getNextFrame returned %i" % ret[0])
            else:
                frameDesc = ret[1]
                print("Software trigger sent to %s return %i" % (hex(hCameras[i]), ret[0]))

            # Note that the frame descriptor has not been modified.
            assert 0.0 == frameDesc.Shutter.fValue

        time.sleep(1) # Wait a second...


def main():

    returnCode = FAILURE

    # First determine how many cameras there are
    numberOfCameras = 0
    ret = PxLApi.getNumberCameras()
    if not PxLApi.apiSuccess(ret[0]):
        print("Error: Unable to determine the number of cameras")
        return FAILURE

    cameraIdInfo = ret[1]

    if 0 == len(cameraIdInfo):
        print("Error: No cameras connected")
        return FAILURE

    # Initialize each of the cameras
    hCameras = []
    for i in range(len(cameraIdInfo)):
        ret = PxLApi.initialize(serialNumber=cameraIdInfo[i].CameraSerialNum)
        if not PxLApi.apiSuccess(ret[0]):
            print("Error: Unable to initialize camera %i" % cameraIdInfo[i].CameraSerialNum)
        if PxLApi.apiSuccess(ret[0]):
            hCamera = ret[1]
            ret = prepare_camera_for_test(hCamera)
            if PxLApi.apiSuccess(ret[0]):
                print("Camera %i has handle %i" % (cameraIdInfo[i].CameraSerialNum, hCamera))
                hCameras.append(hCamera)
            else:
                print("Error: Unable to prepare camera %i" % cameraIdInfo[i].CameraSerialNum)
                PxLApi.uninitialize(hCamera)
                break

    # Did we initialize all of them successfully?
    if len(hCameras) == len(cameraIdInfo):
        numberOfCapturesToDo = 5
        do_test(hCameras, numberOfCapturesToDo)
        returnCode = SUCCESS

    for i in range(len(hCameras)):
        PxLApi.setCallback(hCameras[i], PxLApi.Callback.FRAME, 0, None)
        PxLApi.setStreamState(hCameras[i], PxLApi.StreamState.STOP)
        PxLApi.uninitialize(hCamera)

    return returnCode


if __name__ == "__main__":
    main()
