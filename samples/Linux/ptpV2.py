"""
ptpV2.py

Demonstration of a trivial interaction with the Pixelink API

More specifically, this demo will demonstarte how to use IEEE 1588 (PTPv2)
on a Pixelink camera. This demo program has minimal error handling, as its 
purpose is to show minimal code to interact with the Pixelink API, not tell 
you how to do your error handling.

With this program, we assume that there is at least one camera connected, 
and that no cameras are connected or disconnected while the program is 
running.
"""

from pixelinkWrapper import*
import time

EXIT_SUCCESS = 0
EXIT_FAILURE = 1


def transitory_ptp_state(state):

    # Returns True if the PTP state machine is in a transitory (non-stable) state
    switcher = {
        PxLApi.PtpStatus.INITIALIZING: True,
        PxLApi.PtpStatus.FAULTY: False,
        PxLApi.PtpStatus.DISABLED: False,
        PxLApi.PtpStatus.LISTENING: True,
        PxLApi.PtpStatus.PREMASTER: True,
        PxLApi.PtpStatus.MASTER: False,
        PxLApi.PtpStatus.PASSIVE: False,
        PxLApi.PtpStatus.UNCALIBRATED: True,
        PxLApi.PtpStatus.SLAVE: False,     
        }
    return switcher.get(state, False)


def main():

    # Initialize any camera
    ret = PxLApi.initialize(0)
    if not PxLApi.apiSuccess(ret[0]):
        print("Error: Unable to initialize a camera: rc=%d" % ret[0])
        return EXIT_FAILURE

    hCamera = ret[1]

    # do a get on the feature, mostly to make sure the camera supports it.
    ptpParams = [0] * PxLApi.PtpParams.NUM_PARAMS

    ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.PTP, ptpParams)
    if not PxLApi.apiSuccess(ret[0]):
        print("Error: Unable to get FEATURE_PTP for the camera: rc=%d" % ret[0])
        PxLApi.uninitialize(hCamera)
        return EXIT_FAILURE

    print("Enabling PTP Auto mode, and waiting for clock synchronization...")

    ptpParams[PxLApi.PtpParams.MODE] = PxLApi.PtpModes.AUTOMATIC
    ret = PxLApi.setFeature(hCamera, PxLApi.FeatureId.PTP, PxLApi.FeatureFlags.AUTO, ptpParams)
    if not PxLApi.apiSuccess(ret[0]):
        print("Error: Unable to set FEATURE_PTP for the camera: rc=%d" % ret[0])
        PxLApi.uninitialize(hCamera)
        return EXIT_FAILURE

    while(True):

        ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.PTP)
        if not PxLApi.apiSuccess(ret[0]):
            print("Error: Unable to get FEATURE_PTP for the camera: rc=%d" % ret[0])
            PxLApi.uninitialize(hCamera)
            return EXIT_FAILURE

        ptpParams = ret[2]
        print("    \r Current PTP state:%d" % ptpParams[PxLApi.PtpParams.STATUS], end="")
        if not transitory_ptp_state(ptpParams[PxLApi.PtpParams.STATUS]):
            break

        time.sleep(0.250) # Take a breather

    print("\n PTP Info:")
    print("    Mode: %d" % ptpParams[0])
    print("    Status: %d" % ptpParams[1])
    print("    My Clock Accuracy: %.9f" % ptpParams[2])
    print("    Offset From Master: %.9f" % ptpParams[3])

    PxLApi.uninitialize(hCamera)
    return EXIT_SUCCESS

if __name__ == "__main__":
    main()
