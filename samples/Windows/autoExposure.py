"""
autoExposure.py

This demonstrates how to control a camera's autoexposure features.

Option 1) Enable autoexposure (FeatureFlags.AUTO)
When autoexposure is enabled, the camera controls the exposure based on its own internal algorithm.
The exposure will be continuously adjusted over time by the camera until autoexposure is disabled.

Option 2) Autoexpose Once (FeatureFlags.ONEPUSH)
When initiated, the camera will adjust the exposure based on its own internal algorithm. Once
a satisfactory exposure has been determined, the camera will release control of the exposure whereupon
the exposure is now again settable via the API.

Option 3) User/applicaton control (FeatureFlags.MANUAL)
The camera will not make any adjustments to the exposure 'automatically' it will only set
the exposure to a specified value, when told to do so by the application.

With autoexpose once, this application demonstrates how you can either:
A) Initiate autoexpose once, then start polling the camera, looping until the operation is complete.
B) Initiate autoexpose once, and then poll the camera at a regular interval with a timer.

Note that this sample application uses threading library to spawn off a thread to perform a one-time
auto exposure.
"""

from pixelinkWrapper import*
from ctypes import*
import threading
import sys
import time
import ctypes.wintypes
import msvcrt

# Not sure what it is for
def api_range_error(rc):
    return rc == PxLApi.ReturnCode.ApiInvalidParameterError or rc == PxLApi.ReturnCode.ApiOutOfRangeError

# One-time operation state
INACTIVE = 1    # A one-time operation is NOT in progress
INPROGRESS = 2  # A one-time operation IS in progress
STOPPING = 3    # A one-time operation IS in progress, but an abort request has been made.

"""
Preview control thread function
"""
def control_preview_thread(hCamera):
    
    # The preview window will go 'Not Responding' if we do not poll the message pump, and 
    # forward events onto it's handler on Windows.
    user32 = windll.user32
    msg = ctypes.wintypes.MSG()
    pMsg = ctypes.byref(msg)

    # Start the preview (NOTE: camera must be streaming)
    ret = PxLApi.setPreviewState(hCamera, PxLApi.PreviewState.START)
    assert PxLApi.apiSuccess(ret[0]), "%i" % ret[0]
    
    while (PxLApi.PreviewState.START == previewState and PxLApi.apiSuccess(ret[0])):
        if user32.PeekMessageW(pMsg, 0, 0, 0, 1) != 0:            
            user32.TranslateMessage(pMsg)
            user32.DispatchMessageW(pMsg)
    
    # Stop the preview
    ret = PxLApi.setPreviewState(hCamera, PxLApi.PreviewState.STOP)
    assert PxLApi.apiSuccess(ret[0]), "%i" % ret[0]

"""
Returns true if the camera supports one-time auto adjustment and continuous adjustment of the specified feature,
false otherwise
"""
def camera_supports_auto_feature(hCamera, featureId):
    
    # Read the feature information
    ret = PxLApi.getCameraFeatures(hCamera, featureId)
    assert PxLApi.apiSuccess(ret[0]), "getCameraFeatures failed"
    
    cameraFeatures = ret[1]

    # Check the sanity of the return information
    assert 1 == cameraFeatures.uNumberOfFeatures, "Unexpected number of features" # We only asked about one feature...
    assert cameraFeatures.Features[0].uFeatureId == featureId, "Unexpected returned featureId" # ... and that feature is the one requested
    isSupported = ((cameraFeatures.Features[0].uFlags & PxLApi.FeatureFlags.PRESENCE) != 0)
    supportsOneTimeAuto = ((cameraFeatures.Features[0].uFlags & PxLApi.FeatureFlags.ONEPUSH) != 0)
    supportsContinualAuto = ((cameraFeatures.Features[0].uFlags & PxLApi.FeatureFlags.AUTO) != 0)

    if(isSupported and supportsOneTimeAuto and supportsContinualAuto):
        # This app does not need/use these -- but yours might....
        global exposureLimits
        exposureLimits = cameraFeatures.Features[0].Params[0]

    return isSupported and supportsOneTimeAuto and supportsContinualAuto

"""
Create a new one-time autoexposure thread
"""
def create_autoexposure_thread(hCamera):
    return threading.Thread(target=perform_one_time_autoexposure, args=(hCamera,), daemon=True)

"""
One-time autoexposure thread function to perform a one-time autoexposure operation, ending when the operation is complete, 
or until told to abort.
"""
def perform_one_time_autoexposure(hCamera):

    global oneTimeAutoExposure
    oneTimeAutoExposure = INPROGRESS
    print("\n\nStarting one-time autoexposure adjustment.")

    exposure = 0 # Intialize exposure to 0, but this value is ignored when initating auto adjustment.
    params = [exposure] 

    ret = PxLApi.setFeature(hCamera, PxLApi.FeatureId.EXPOSURE, PxLApi.FeatureFlags.ONEPUSH, params)
    if not(PxLApi.apiSuccess(ret[0])):
        print("!! Attempt to set one-time autoexposure returned %i!" % ret[0])
        oneTimeAutoExposure == INACTIVE
        return

    # Now that we have initiated a one-time operation, loop until it is done (or told to abort).
    while oneTimeAutoExposure == INPROGRESS:
        ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.EXPOSURE)
        if PxLApi.apiSuccess(ret[0]):
            flags = ret[1]
            params = ret[2]
            if not (flags & PxLApi.FeatureFlags.ONEPUSH): # the operation completed
                break
        time.sleep(0.25) # Give some time for the one-time operation to complete

    if oneTimeAutoExposure == STOPPING:
        ret = PxLApi.setFeature(hCamera, PxLApi.FeatureId.EXPOSURE, PxLApi.FeatureFlags.MANUAL, params)
        if not(PxLApi.apiSuccess(ret[0])):
            print("!! Attempt to aborted one-time autoexposure returned %i!\n"
                  "It will be aborted when it is completed by the camera." % (ret[0]))
            oneTimeAutoExposure == INACTIVE
            return
        print("\nFinished one-time autoexposure adjustment. Operation aborted.\n")
    else:
        print("\nFinished one-time autoexposure adjustment. Operation completed successfully.\n")

    oneTimeAutoExposure = INACTIVE

    return

"""
If a one-time autoexposure is not already in progress, starts a thread that will perfrom the
one-time autoexposure, exiting when it has completed (or is aborted).
"""
def initiate_one_time_autoexposure(hCamera):
    
    global oneTimeAutoExposure
    if oneTimeAutoExposure == INACTIVE:
        oneTimeThread = None
        oneTimeThread = create_autoexposure_thread(hCamera)
        if None == oneTimeThread:
            print("  !! Could not create a one-time autoexposure thread!")
        else:
            oneTimeThread.start()
    return

"""
If a one-time autoexpose is in progress, stops the thread that is perfroming the
one-time autoexposure, waiting for the thread to exit.
"""
def abort_one_time_autoexposure(hCamera):

    global oneTimeAutoExposure
    if oneTimeAutoExposure == INPROGRESS:
        oneTimeAutoExposure = STOPPING

"""
Manually adjusts the exposure, increasing or decreaing it by 10%
"""
def change_exposure(hCamera, up):

    ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.EXPOSURE)
    if not(PxLApi.apiSuccess(ret[0])):
        print("!! Attempt to get exposure returned %i!" % ret[0])
        return
    
    params = ret[2]
    exposure = params[0]
    if up:
        exposure *= 1.1
    else:
        exposure /= 1.1

    params[0] = exposure

    ret = PxLApi.setFeature(hCamera, PxLApi.FeatureId.EXPOSURE, PxLApi.FeatureFlags.MANUAL, params)
    if (not PxLApi.apiSuccess(ret[0])) and (not api_range_error(ret[0])):
        print("!! Attempt to set exposure returned %i!" % ret[0])

"""
Controls continuous autoexposure
"""
def set_continuous_autoexposure(hCamera, on):

    exposure = 0 # Intialize exposure to 0, but this value is ignored when initating auto adjustment.
    params = [exposure]

    if not on:
        # We are looking to turn off the continual auto exposure, which means we will be manually
        # adjusting it from now on -- including with the below PxLApi.setFeature. So given that we have to
        # set it to someting, read the current value (as set by the camera), and use that value.
        ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.EXPOSURE)
        if not PxLApi.apiSuccess(ret[0]):
            print("!! Attempt to get exposure returned %i!" % ret[0])
            return
        params = ret[2]
        flags = PxLApi.FeatureFlags.MANUAL
    else:
        flags = PxLApi.FeatureFlags.AUTO

    ret = PxLApi.setFeature(hCamera, PxLApi.FeatureId.EXPOSURE, flags, params)
    if not PxLApi.apiSuccess(ret[0]):
        print("!! Attempt to set continuous autoexposure returned %i!" % ret[0])
        return

"""
Prints out the current exposure value, and a message if the camera is currently adjusting it.
"""
def print_exposure(hCamera):

    ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.EXPOSURE)
    assert PxLApi.apiSuccess(ret[0]), "%i" % ret[0]
    
    flags = ret[1]
    if flags & PxLApi.FeatureFlags.AUTO:
        adjustmentType = "Continuous  "
    else:
        if flags & PxLApi.FeatureFlags.ONEPUSH:
            adjustmentType = "One-time    "
        else:
            adjustmentType = "Manual      "
    
    params = ret[2]
    exposure = round(params[0]*1000, 3)
    
    print("\rExposure: %i milliseconds, Adjustment type: %s" % (exposure, adjustmentType), end="")


def main():

    global previewState # Controls preview thread
    done = False

    ret = PxLApi.initialize(0)
    if not(PxLApi.apiSuccess(ret[0])):
        print("Could not initialize the camera! rc = %i" % ret[0])
        return 1

    hCamera = ret[1]
    
    if not(camera_supports_auto_feature(hCamera, PxLApi.FeatureId.EXPOSURE)):
        print("Camera does not support Auto Exposure")
        PxLApi.uninitialize(hCamera)
        return 1

    print("Starting the stream for camera with handle: %i" % hCamera);
    print("    q   : to quit");
    print("    +   : to increase exposure by 10%");
    print("    -   : to decrease exposure by 10%");
    print("    c   : to turn ON continuous autoexposure");
    print("    C   : to turn OFF continuous autoexposure (so will +, -, or o)");
    print("    o   : to perform a one-time autoexposure operation\n");
    print("NOTE: pressing any key will abort any one-time autoexposure in progress\n");
    
    # Start the stream
    ret = PxLApi.setStreamState(hCamera, PxLApi.StreamState.START)
    if not(PxLApi.apiSuccess(ret[0])):
        print("Could not start the stream! rc = %i" % ret[0])
        PxLApi.uninitialize(hCamera)
        return 1

    # Start preview
    previewState = PxLApi.PreviewState.START
    # Declare control preview thread that can control preview and poll the message pump on Windows
    previewThread = threading.Thread(target=control_preview_thread, args=(hCamera,), daemon=True)
    previewThread.start()
    
    while not(done):
        sys.stdin.flush()
        if msvcrt.kbhit():
            keyPressed = kbHit()
            abort_one_time_autoexposure(hCamera)
            if 'q' == keyPressed or 'Q' == keyPressed:
                print("\r")
                done = True
            elif '+' == keyPressed or '-' == keyPressed:
                change_exposure(hCamera, '+' == keyPressed)                
            elif 'c' == keyPressed:
                set_continuous_autoexposure(hCamera, True)
            elif 'C' == keyPressed:
                set_continuous_autoexposure(hCamera, False)
            elif 'o' == keyPressed or 'O' == keyPressed:
                initiate_one_time_autoexposure(hCamera)
        if not(done):
            print_exposure(hCamera)
            time.sleep(0.1) # 100 ms
        else:
            sys.stdout.flush()
    
    # Stop preview
    previewState = PxLApi.PreviewState.STOP

    PxLApi.setStreamState(hCamera, PxLApi.StreamState.STOP)

    PxLApi.uninitialize(hCamera)
    
    return 0

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
    # Global to remember the exposure limits. Set with a succesful call to camera_supports_auto_feature
    # Note that this application doesn't actually use these -- but your application might find
    # this information useful.
    exposureLimits = None
    previewState = PxLApi.PreviewState.STOP # control preview thread
    oneTimeAutoExposure = INACTIVE # Controls one-time auto exposure thread
    main()
