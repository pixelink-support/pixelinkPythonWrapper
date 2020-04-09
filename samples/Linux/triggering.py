"""
triggering.py

A simple example of the use of the two triggering types: 
  software
  hardware
 
Note 1: This application assumes that a camera that is capable of
hardware triggering (IE, it supports hardware triggering), is capable
of receiving a hardware trigger (IE, it has a 'hardware trigger jig'
connected).

Note 2: We do NOT explore here the triggering modes such as 
Mode 0 vs Mode 14 et cetera. The Pixelink documentation provides 
details about the various triggering modes.

Note 3: We assume that there's only one Pixelink camera connected to 
the computer.
"""

from pixelinkWrapper import*
from ctypes import*

SUCCESS = 0
FAILURE = 1

"""
Not all Pixelink cameras support triggering.
Machine vision cameras support triggering, but microscopy cameras do not.
"""
def is_triggering_supported(hCamera):

    # Read the trigger feature information
    ret = PxLApi.getCameraFeatures(hCamera, PxLApi.FeatureId.TRIGGER)
    assert PxLApi.apiSuccess(ret[0])

    cameraFeatures = ret[1]
    # Check the sanity of the return information
    assert 1 == cameraFeatures.uNumberOfFeatures                                # We only asked about one feature...
    assert PxLApi.FeatureId.TRIGGER == cameraFeatures.Features[0].uFeatureId    # ... and that feature is triggering
    
    isSupported = ((cameraFeatures.Features[0].uFlags & PxLApi.FeatureFlags.PRESENCE) != 0)
    if isSupported:
        # While we're here, check an assumption about the number of parameters
        assert PxLApi.TriggerParams.NUM_PARAMS == cameraFeatures.Features[0].uNumberOfParameters
    
    return isSupported

"""
Sets flags to enable/disable a feature
"""
def enable_feature(flags, enable):
    if enable:
        flags = ~PxLApi.FeatureFlags.MOD_BITS | PxLApi.FeatureFlags.MANUAL
    else:
        flags = ~PxLApi.FeatureFlags.MOD_BITS | PxLApi.FeatureFlags.OFF
    return flags


def disable_triggering(hCamera):

    # Read current settings
    ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.TRIGGER)
    assert PxLApi.apiSuccess(ret[0])
    flags = ret[1]
    params = ret[2]
    assert 5 == len(params)

    # Disable triggering
    flags = enable_feature(flags, False)

    ret = PxLApi.setFeature(hCamera, PxLApi.FeatureId.TRIGGER, flags, params)
    assert PxLApi.apiSuccess(ret[0])

"""
Set up the camera for triggering, and enable triggering.
"""
def set_triggering(hCamera, mode, triggerType, polarity, delay, param):

    # Read current settings
    ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.TRIGGER)
    assert PxLApi.apiSuccess(ret[0])
    flags = ret[1]
    params = ret[2]
    assert 5 == len(params)
    
    # Very important step: Enable triggering by clearing the FEATURE_FLAG_OFF bit
    flags = enable_feature(flags, True)

    # Assign the new values...
    params[PxLApi.TriggerParams.MODE] = mode
    params[PxLApi.TriggerParams.TYPE] = triggerType
    params[PxLApi.TriggerParams.POLARITY] = polarity
    params[PxLApi.TriggerParams.DELAY] = delay
    params[PxLApi.TriggerParams.PARAMETER] = param

    # ... and write them to the camera
    ret = PxLApi.setFeature(hCamera, PxLApi.FeatureId.TRIGGER, flags, params)
    assert PxLApi.apiSuccess(ret[0])

"""
Quick and dirty routine to capture an image (and do nothing with it)
"""
def capture_image(hCamera):

    # Large buffer that will handle all currently supported cameras in 16-bit mode
    frame = create_string_buffer(5000 * 5000 * PxLApi.getBytesPerPixel(PxLApi.PixelFormat.BAYER16))

    ret = PxLApi.getNextFrame(hCamera, frame)
    assert PxLApi.apiSuccess(ret[0])
    print("Image captured.")

"""
With software triggering, calling PxLApi.getNextFrame causes the camera to capture an image.
The camera must be in the streaming state, but no image will be 'streamed' to the host
until PxLApi.getNextFrame is called.
"""
def test_software_trigger(hCamera):
    
    print("\nConfiguring the camera for software triggering")

    set_triggering(hCamera,
        PxLApi.TriggerModes.MODE_0,     # Mode 0 Triggering
        PxLApi.TriggerTypes.SOFTWARE,
        PxLApi.Polarity.ACTIVE_LOW,
        0.0,                            # no delay
        0)                              # unused for Mode 0

    ret = PxLApi.setStreamState(hCamera, PxLApi.StreamState.START)
    assert PxLApi.apiSuccess(ret[0])

    # We can now grab two images (without blocking)
    print("Capturing two images...")
    capture_image(hCamera)
    capture_image(hCamera)
    print("done")

    ret = PxLApi.setStreamState(hCamera, PxLApi.StreamState.STOP)
    assert PxLApi.apiSuccess(ret[0])

"""
With hardware triggering, the camera doesn't take an image until the trigger input of 
the machine vision connector is activated. 
"""
def test_hardware_trigger(hCamera):

    print("\nConfiguring the camera for hardware triggering...")

    set_triggering(hCamera,
        PxLApi.TriggerModes.MODE_0,     # Mode 0 Triggering
        PxLApi.TriggerTypes.HARDWARE,
        PxLApi.Polarity.ACTIVE_LOW,
        0.0,                            # no delay
        0)                              # unused for Mode 0

    ret = PxLApi.setStreamState(hCamera, PxLApi.StreamState.START)
    assert PxLApi.apiSuccess(ret[0])

    print("Waiting for a hardware trigger...")
    capture_image(hCamera)
    print("Waiting for one more hardware trigger...")
    capture_image(hCamera)
    print("done")

    ret = PxLApi.setStreamState(hCamera, PxLApi.StreamState.STOP)
    assert PxLApi.apiSuccess(ret[0])


def main():

    # Initialize any camera
    ret = PxLApi.initialize(0)
    if not(PxLApi.apiSuccess(ret[0])):
        print("ERROR Unable to initialize a camera")
        return FAILURE

    hCamera = ret[1]

    # If the camera doesn't support triggering, we're done.
    if not is_triggering_supported(hCamera):
        print("Triggering is not supported on this camera")
        PxLApi.uninitialize(hCamera)
        return FAILURE

    # Start with triggering disabled so we start with a clean slate
    disable_triggering(hCamera)   
    # Test the three major types of triggering
	# We only use Mode 0 triggering.
    test_software_trigger(hCamera)
    test_hardware_trigger(hCamera)

    # Put the camera back to a known state
    disable_triggering(hCamera)

    PxLApi.uninitialize(hCamera)
    return SUCCESS


if __name__ == "__main__":
    main()
