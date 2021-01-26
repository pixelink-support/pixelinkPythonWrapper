"""
frameActions.py 

Demonstration application showing how to use Frame Action type Triggering
 
Frame action triggering is particularly useful when you need to grab images
from multiple cameras simultanesouly -- either at a time as directed by
a host appliction (kind of like a multi-camera software trigger), or at
a user specified time.

This particular example requires there be 2 or more cameras connected, and
that these cameras support PTP (Percersion Time Protocol V2, AKA IEEE1588), and
that the time is synchronized between the cameras (all cameras are either a PTP 
Master or Slave).
"""

from pixelinkWrapper import*
import time

EXIT_SUCCESS = 0
EXIT_FAILURE = 1

ACTION_DELAY = 5.0 # 5 seconds

@PxLApi._dataProcessFunction
def frame_callback_func(hCamera, frameData, dataFormat, frameDesc, userData):

    # We will print out the frame time. If all of the cameras are identically configured, then the
    # frame time of each of the images should be identical. However, if the cameras are of different
    # models, or are configured differently, then the frame time will vary. The frame time is 
    # 'latched' as the first pixel of the image is received from the imaging sensor, which 
    # would be after the camera's exposure (AKA shutter) time.
    #
    # For example, say we had 2 identical models of camera, each configured identically except for
    # exposure; Camera A is using an exposure of 20 ms, while camera B is using an exposure of 120 ms.
    # In this example, you can expect the timestamps of the images returned from camera A and camera B
    # to differ by 100 ms.
    
    # Copy frame descriptor information
    frameDescriptor = frameDesc.contents
    print("       FrameCallbackFunction: camera=%d, exposure=%6.2f (ms) frameTime=%6.3f" %
          (gSerials[hCamera], frameDescriptor.Shutter.fValue * 1000, frameDescriptor.dFrameTime))
    return PxLApi.ReturnCode.ApiSuccess


def ptp_synchronized(hCamera):

    ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.PTP)
    if PxLApi.apiSuccess(ret[0]):
        ptpParams = ret[2]
        if (ptpParams[PxLApi.PtpParams.STATUS] == PxLApi.PtpStatus.MASTER or \
            ptpParams[PxLApi.PtpParams.STATUS] == PxLApi.PtpStatus.SLAVE):
            return True

    return False


def main():

    numPtpSynchedCameras = 0

    # Step 1
    # Ensure there at least 2 cameras connected
    ret = PxLApi.getNumberCameras()
    if not PxLApi.apiSuccess(ret[0]):
        print("ERROR: Could not find any cameras (%d)" % ret[0])
        return EXIT_FAILURE

    numCameras = ret[1]
    if len(numCameras) < 2:
        print("ERROR: There must be at least 2 cameras connected")
        return EXIT_FAILURE

    triggerParams = [0] * PxLApi.TriggerParams.NUM_PARAMS

    # For each of the ptp synchronized cameras...
    myCameras = list()
    for cameraIdInfo in numCameras:

        # Step 2
        # Initialize the camera, and check to see if it is PTP synchronized
        ret = PxLApi.initialize(cameraIdInfo.CameraSerialNum)
        if PxLApi.apiSuccess(ret[0]):
            hCamera = ret[1]

            if ptp_synchronized(hCamera):
                numPtpSynchedCameras += 1
                gSerials.__setitem__(hCamera, cameraIdInfo.CameraSerialNum)
                
                # Step 3
                # Register a frame callback for this camera
                ret = PxLApi.setCallback(hCamera, PxLApi.Callback.FRAME, 0, frame_callback_func)
                if not PxLApi.apiSuccess(ret[0]):                   # Error handling
                    print("PxLSetCallback rc:%d" % ret[0])

                # Step 4
                # Set up a Frame Action Trigger
                triggerParams[PxLApi.TriggerParams.TYPE] = PxLApi.TriggerTypes.ACTION
                ret = PxLApi.setFeature(hCamera, PxLApi.FeatureId.TRIGGER, PxLApi.FeatureFlags.MANUAL, triggerParams)
                if not PxLApi.apiSuccess(ret[0]):                   # Error handling
                    print("PxLSetFeature Trigger rc:%d" % ret[0])
                
                # Step 5
                # Start the stream
                ret = PxLApi.setStreamState(hCamera, PxLApi.StreamState.START)

            myCameras.append(hCamera)   # 'remember' this camera

    print("Found %d PTP synched cameras" % numPtpSynchedCameras)

    # Step 6
    # All ptp synchronized cameras are waiting for a frame event -- send one now.
    print("   You should see one image from each of %d cameras, immediatly..." % numPtpSynchedCameras)
    ret = PxLApi.setActions(PxLApi.ActionTypes.FRAME_TRIGGER, 0)
    
    # Step 7
    # All ptp synchronized cameras are waiting for a frame event -- send one that matures in ACTION_DELAY seconds.
    print("   You should see one image from each of %d cameras, after %3.1f seconds..." % (numPtpSynchedCameras, ACTION_DELAY))
    ret = PxLApi.getCurrentTimestamp(hCamera)

    if PxLApi.apiSuccess(ret[0]):
        currentTime = ret[1]
        ret = PxLApi.setActions(PxLApi.ActionTypes.FRAME_TRIGGER, currentTime+ACTION_DELAY)
    
    # Delay waiting for the action
    time.sleep(ACTION_DELAY*2)

    # Step 8
    # Cleanup
    for i in range(len(myCameras)):
        PxLApi.setStreamState(myCameras[i], PxLApi.StreamState.STOP)
        PxLApi.setFeature(myCameras[i], PxLApi.FeatureId.TRIGGER, PxLApi.FeatureFlags.OFF, triggerParams)
        PxLApi.uninitialize(myCameras[i])

    return EXIT_SUCCESS

if __name__ == "__main__":
    # Use a global dictionary to keep track of camera serail numbers (by camera handle)
    gSerials = dict()
    main()
