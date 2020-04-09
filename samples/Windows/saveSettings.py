"""
saveSettings.py

This demonstrates how save camera settings in non-volatile store, as well as restoring
a camera back to using its factory default settings.

More specifically, is howcases how to use:
    - PxLApi.saveSettings
    - PxLApi.loadSettings

NOTE: This application assumes there is at most, one Pixelink camera connected to the system
"""

from pixelinkWrapper import*
import msvcrt
import time

# A few useful constants
WAIT_TIME = 30 # total wait time for a camera to finish a power cycle (in seconds)
POLL_INTERVAL = 1 # Time between polls to see if a camera has finished a power cycle (in seconds)


def main():

    # Step 1
    # Find, and initialize, a camera
    ret = PxLApi.initialize(0)
    if not(PxLApi.apiSuccess(ret[0])):
        print("Could not Initialize the camera! rc = %i" % ret[0])
        return 1
    hCamera = ret[1]

    print("\nWARNING: This application will restore the connected camera back to it's factory default settings")
    print("   Ok to proceed (y/n)? ")

    keyPressed = kbHit()
    
    if 'y' != keyPressed and 'Y' != keyPressed:
        # User aborted.
        PxLApi.uninitialize(hCamera)
        return 1

    # Step 2
    # Restore the camera back to it's factory default settings, and report the expsoure
    ret = PxLApi.loadSettings(hCamera, PxLApi.Settings.SETTINGS_FACTORY)
    assert PxLApi.apiSuccess(ret[0])
    ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.EXPOSURE)
    assert PxLApi.apiSuccess(ret[0])
    params = ret[2]
    factoryDefaultExposure = params[0]
    print(" Exposure: %5.2f ms <-- factory default value." % (factoryDefaultExposure*1000))

    # Step 3
    # Change the exposure.  We'll choose a value that is 10% longer, and save the camera settings
    # to non-volatile store.
    currentExposure = factoryDefaultExposure * 1.1
    params[0] = currentExposure
    ret = PxLApi.setFeature(hCamera, PxLApi.FeatureId.EXPOSURE, PxLApi.FeatureFlags.MANUAL, params)
    assert PxLApi.apiSuccess(ret[0])
    ret = PxLApi.saveSettings(hCamera, PxLApi.Settings.SETTINGS_USER)
    assert PxLApi.apiSuccess(ret[0])

    # Step 4
    # Have the user power cycle the camera.
    # Do an uninitialize of the camera first, so some cleanup can be done.
    PxLApi.uninitialize(hCamera)
    print(" Exposure: %5.2f ms <-- user set value. Please power cycle the camera. Press a key "
          "when you are done." % (currentExposure*1000), flush=True)
    kbHit()
    print("\nWaiting for the camera to finish initializing", end="", flush=True)

    # Step 5
    # Wait for the camera to reappear, but don't wait forever
    waitTime = 0
    while waitTime < WAIT_TIME:
        ret = PxLApi.initialize(0)
        if PxLApi.apiSuccess(ret[0]):
            hCamera = ret[1]
            break
        print(".", end="", flush=True)
        # Recheck for the camera from time to time
        waitTime += POLL_INTERVAL
        time.sleep(POLL_INTERVAL)
    print("done")
    assert waitTime < WAIT_TIME
    
    # Step 6
    # Report the camera's exposure. It should still be the user set value
    ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.EXPOSURE)
    assert PxLApi.apiSuccess(ret[0])
    params = ret[2]
    currentExposure = params[0]
    print(" Exposure: %5.2f ms <-- non-volatile user set value." % (currentExposure*1000))
    assert currentExposure != factoryDefaultExposure

    # Step 7
    # Restore the camera back to factory defaults, and then save these defaults to non-volatile store.
    ret = PxLApi.loadSettings(hCamera, PxLApi.Settings.SETTINGS_FACTORY)
    assert PxLApi.apiSuccess(ret[0])
    ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.EXPOSURE)
    assert PxLApi.apiSuccess(ret[0])
    params = ret[2]
    factoryDefaultExposure = params[0]
    ret = PxLApi.saveSettings(hCamera, PxLApi.Settings.SETTINGS_USER)
    assert PxLApi.apiSuccess(ret[0])

    # Step 8
    # Have the user power cycle the camera. 
    # Do an uninitialize of the camera first, so some cleanup can be done.
    PxLApi.uninitialize(hCamera)
    print(" Exposure: %5.2f ms <-- factory default value. Please power cycle the camera and press a key "
          "when you are done. " % (factoryDefaultExposure*1000), flush=True)
    kbHit()
    print("\nWaiting for the camera to finish initializing", end="", flush=True)

    # Step 9
    # Wait for the camera to reappear, but don't wait forever
    waitTime = 0
    while waitTime < WAIT_TIME:
        ret = PxLApi.initialize(0)
        if PxLApi.apiSuccess(ret[0]):
            hCamera = ret[1]
            break
        print(".", end="", flush=True)
        # Recheck for the camera from time to time
        waitTime += POLL_INTERVAL
        time.sleep(POLL_INTERVAL)
    print("done")
    assert waitTime < WAIT_TIME

    # Step 10
    # Report the camera's exposure.  It should still be the factory default value again
    ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.EXPOSURE)
    assert PxLApi.apiSuccess(ret[0])
    params = ret[2]
    currentExposure = params[0]
    print(" Exposure: %5.2f ms <-- non-volatile factory default value." % (currentExposure*1000))
    assert currentExposure == factoryDefaultExposure

    # Step 11
    # Done.
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
    main()
