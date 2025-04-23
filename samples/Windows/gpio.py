"""
gpio.py

This demonstrates how to control a camera's general purpose input (GPI), and general purpose output (GPO).

This sample works with all Firewire/USB/USB3/GigE/10GigE cameras, provided the camera has at least one GPI 
and a GPO. It also interrogates the camera to determine the camera’s specific GPIO capability/properties.

If the camera has at least one GPI and a GPO, they will be set. Then, the program will poll the GPI value, 
reporting on the value on the console, and on the GPO.
"""

from pixelinkWrapper import*
import msvcrt
import time

# A few useful defines
GPIO_ON = True
GPIO_OFF = False

# The poll period of the GPI, in seconds
POLL_PERIOD_SEC = 0.5

"""
Returns true if the camera has a GPI and a GPO
"""
def supports_gpio(hCamera):
    # GPIO index supporting GPI
    global gpiIndex

    # Step 1
    # Get info on the GPIO for this camera
    ret = PxLApi.getCameraFeatures(hCamera, PxLApi.FeatureId.GPIO)
    if not PxLApi.apiSuccess(ret[0]):
        return False
    gpioFeatureInfo = ret[1]

    # Step 2
    # Look at the feature info, and ensure the camera supports a GPI and a GPO
    if not gpioFeatureInfo.Features[0].uFlags & PxLApi.FeatureFlags.PRESENCE:       # No GPIOs at all !!
        return False
    if gpioFeatureInfo.Features[0].Params[0].fMaxValue < 2.0:                       # We need at least 2 GPIO !!
        return False
    if gpioFeatureInfo.Features[0].Params[1].fMaxValue < PxLApi.GpioModes.INPUT:    # Does not support GPI !!
        return False
    if gpioFeatureInfo.Features[0].Params[0].fMaxValue == 3.0:                      # For PL-X cameras
        gpiIndex = 3.0
    else:                                                                           # For PL-D and other cameras
        gpiIndex = 1.0
    
    return True



def setup_gpios(hCamera):

    gpioParams = [0] * PxLApi.GpioParams.NUM_PARAMS
    # Step 1
    # Set the GPI
    gpioParams[PxLApi.GpioParams.INDEX] = gpiIndex
    gpioParams[PxLApi.GpioParams.MODE] = PxLApi.GpioModes.INPUT
    gpioParams[PxLApi.GpioParams.POLARITY] = 0
    # Don't care about the other parameters
    ret = PxLApi.setFeature(hCamera, PxLApi.FeatureId.GPIO, PxLApi.FeatureFlags.MANUAL, gpioParams)
    if not PxLApi.apiSuccess(ret[0]):
        return ret

    # Step 2
    # Set the GPO (to normal mode)
    gpioParams[PxLApi.GpioParams.INDEX] = 2.0
    gpioParams[PxLApi.GpioParams.MODE] = PxLApi.GpioModes.NORMAL
    gpioParams[PxLApi.GpioParams.POLARITY] = 0
    # Don't care about the other parameters
    ret = PxLApi.setFeature(hCamera, PxLApi.FeatureId.GPIO, PxLApi.FeatureFlags.MANUAL, gpioParams)
    
    return ret


def main():

    gpioParams = [0] * PxLApi.GpioParams.NUM_PARAMS

    # Step 1
    # Find and initialize a camera
    ret = PxLApi.initialize(0)
    if not(PxLApi.apiSuccess(ret[0])):
        print("Could not Initialize the camera! Rc = %i" % ret[0])
        return 1

    hCamera = ret[1]

    # Step 2
    # Ensure the camera has at least 2 gpios, and supports a GPI
    if not supports_gpio(hCamera):
        print("Camera does not support GPIO!")
        PxLApi.uninitialize(hCamera)
        return 1
    
    # Step 3
    # Set the camera up for one GPI and one GPO
    ret = setup_gpios(hCamera)
    if not PxLApi.apiSuccess(ret[0]):
        print("Could not setup the GPIOs! Rc = %i" % ret[0])
        PxLApi.uninitialize(hCamera)
        return 1

    # Give the last GPI a value that will ensure our loop will print/assert the GPO on its first time through
    lastGpi = GPIO_ON

    # Step 4
    # Poll the GPI, reporting it's value on the console, and on the GPO
    print("Polling the GPI every %i ms, press any key to exit" % (POLL_PERIOD_SEC*1000))
    while not msvcrt.kbhit():
        # Read the GPI
        gpioParams[PxLApi.GpioParams.INDEX] = gpiIndex
        ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.GPIO, gpioParams)
        if not PxLApi.apiSuccess(ret[0]):
            print("\nCould not read the GPI! Rc = %i" % ret[0])
            PxLApi.uninitialize(hCamera)
            return 1
        gpioParams = ret[2]

        if 0 == gpioParams[PxLApi.GpioModeInput.STATUS]:
            currentGpi = GPIO_OFF
        else:
            currentGpi = GPIO_ON

        # If the GPI changed, then set the GPO

        if currentGpi != lastGpi:

            gpioParams[PxLApi.GpioParams.INDEX] = 2.0
            gpioParams[PxLApi.GpioParams.MODE] = PxLApi.GpioModes.NORMAL
            gpioParams[PxLApi.GpioParams.POLARITY] = float(currentGpi)
            # Don't care about the other parameters
            ret = PxLApi.setFeature(hCamera, PxLApi.FeatureId.GPIO, PxLApi.FeatureFlags.MANUAL, gpioParams)
            if not PxLApi.apiSuccess(ret[0]):
                print("\nCould not write the GPO! Rc = %i" % ret[0])
                PxLApi.uninitialize(hCamera)
                return 1

            lastGpi = currentGpi
        
        if GPIO_ON == currentGpi:
            currentGpiState = "On"
        else:
            currentGpiState = "Off"
        print("\rGPI is %s   " % currentGpiState, end="", flush=True)

        time.sleep(POLL_PERIOD_SEC) # 500 ms

    PxLApi.uninitialize(hCamera)
    return 0


if __name__ == "__main__":
    gpiIndex = 0.0          # GPIO index supporting GPI depending on the camera model
    main()