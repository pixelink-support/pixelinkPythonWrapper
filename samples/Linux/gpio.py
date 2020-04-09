"""
gpio.py

This demonstrates how to control a camera's general purpose input (gpi), and general purpose output (gpo).

This program will setup the first GPIO as an 'input', and the second GPO as an 'output'. It will then
poll the GPI value, reporting on the value on the console, and on the GPO.
"""

from pixelinkWrapper import*
from select import select
import sys
import time
import tty
import termios

# A few useful defines
GPIO_ON = True
GPIO_OFF = False

# The poll period of the GPI, in seconds
POLL_PERIOD_SEC = 0.5

"""
Returns true if the camera has a GPI and a GPO
"""
def supports_gpio(hCamera):

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
    
    return True


def setup_gpios(hCamera):

    gpioParams = [0] * PxLApi.GpioParams.NUM_PARAMS
    # Step 1
    # Setup GPIO #1 for input
    gpioParams[PxLApi.GpioParams.INDEX] = 1.0 # The first GPIO
    gpioParams[PxLApi.GpioParams.MODE] = PxLApi.GpioModes.INPUT
    gpioParams[PxLApi.GpioParams.POLARITY] = 0
    # Don't care about the other parameters
    ret = PxLApi.setFeature(hCamera, PxLApi.FeatureId.GPIO, PxLApi.FeatureFlags.MANUAL, gpioParams)
    if not PxLApi.apiSuccess(ret[0]):
        return ret

    # Step 2
    # Setup GPIO #2 for manual output
    gpioParams[PxLApi.GpioParams.INDEX] = 2.0 # The first GPIO
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
    # Ensure the camera has at least 2 gpos, and supports a GPI (which is always the first GPIO)
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

    # give the last GPI a value that will ensure our loop will print/assert the GPO on its first time through
    lastGpi = GPIO_ON

    # Step 4
    # Poll the GPI (the first GPIO), reporting it's value on the console, and on the GPO (the second GPIO) 
    print("Polling the GPI every %i ms, press any key to exit" % (POLL_PERIOD_SEC*1000))
    setUnbufKb(True)
    while not kbhit():
        # Read the GPI
        gpioParams[PxLApi.GpioParams.INDEX] = 1.0
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

    setUnbufKb(False)
    print("\r")
    PxLApi.uninitialize(hCamera)
    return 0

"""
Unbuffered non-blocking keyboard input on command line.
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

# Unbuffered button hit
def kbhit():
    btnHit = False
    rlist = select([sys.stdin], [], [], 0)
    if rlist[0] != []:
        sys.stdin.read(1)
        btnHit = True
    return btnHit


if __name__ == "__main__":
    main()
