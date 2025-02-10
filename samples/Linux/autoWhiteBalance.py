"""
autoWhiteBalance.py 

A simple little application to perform an auto white balance.

Note1: This program does a 'directed' auto white balance. That is, it uses
the FeatureId.AUTO_ROI to provide guiadance to the auto white balance algorithm, 
where to find 'white' in the image. If this feature is not used, then the 
camera will search the entire image, lookng for what it believes to be 'white'.

Note2: The sample application 'whiteBalance' does not use the FeatureId.AUTO_ROI.

Note3: The sample applicaiton 'autoExposure' shows how to cancel an auto operation.
"""

from pixelinkWrapper import*
import time

"""
Simple function to abort an auto white balance
"""
def abort_auto_white_balance(hCamera):

    rgbGains = (1, 1, 1) # We need to set them to something -- unity is a nice simple value

    ret = PxLApi.setFeature(hCamera, PxLApi.FeatureId.WHITE_SHADING, PxLApi.FeatureFlags.MANUAL, rgbGains)
    if not(PxLApi.apiSuccess(ret[0])):
        print("  Error - setFeature to cancel AutoWB returned %i" % ret[0])


def main():

    # Step 1 - Grab a camera.
    ret = PxLApi.initialize(0)
    if not(PxLApi.apiSuccess(ret[0])):
        print("  Error - initialize returned %i" % ret[0])
        return 1

    hCamera = ret[1]

    # Step 2 - Get the current ROI
    ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.ROI)
    if not(PxLApi.apiSuccess(ret[0])):
        print("  Error - getFeature(FeatureId.ROI) returned %i" % ret[0])
        PxLApi.uninitialize(hCamera)
        return 1

    params = ret[2]

    # Step 3 - Set the AUTO_ROI to a 256x256 window in the centre of the ROI
    params[0] = (params[2] - 256)/2
    params[1] = (params[3] - 256)/2
    params[2] = params[3] = 256
    ret = PxLApi.setFeature(hCamera, PxLApi.FeatureId.AUTO_ROI, PxLApi.FeatureFlags.MANUAL, params)
    if not(PxLApi.apiSuccess(ret[0])):
        print("  Error - setFeature(FeatureId.AUTO_ROI) returned %i" % ret[0])
        PxLApi.uninitialize(hCamera)
        return 1

    # Step 4 - Perform a one-time, auto white balance
    params[0] = params[1] = params[2] = 1
    ret = PxLApi.setFeature(hCamera, PxLApi.FeatureId.WHITE_SHADING, PxLApi.FeatureFlags.ONEPUSH, params)
    if not(PxLApi.apiSuccess(ret[0])):
        print("  Error - setFeature(FeatureId.WHITE_SHADING) returned %i" % ret[0])
        PxLApi.uninitialize(hCamera)
        return 1

    # Step 5 - Perform a one-time, auto white balance
    print("Waiting on White Balance to complete")

    for i in range(waitSeconds):
        ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.WHITE_SHADING)
        flags = ret[1]
        params = ret[2]
        if not(flags & PxLApi.FeatureFlags.ONEPUSH):
            break
        print("Interim balance --> R:%f, G:%f, B:%f" % (params[0], params[1], params[2]))
        time.sleep(1)
        waitedForSeconds = i

    if not(PxLApi.apiSuccess(ret[0])):
        print("  Error - getFeature(FeatureId.WHITE_SHADING) returned %i" % ret[0])
        abort_auto_white_balance(hCamera)
        PxLApi.uninitialize(hCamera)
        return 1
    
    # The auto white balance completed successfully or with a warning -- or we got tired of waiting.
    if waitSeconds == (waitedForSeconds + 1):
        print("Tired of waiting on the white balance, aborting it")
        abort_auto_white_balance(hCamera)
    else:
        print("Final balance --> R:%f, G:%f, B:%f" % (params[0], params[1], params[2]))

    # Step 6 - Cleanup
    PxLApi.uninitialize(hCamera)

    return 0


if __name__ == "__main__":
    waitSeconds = 10 # Wait this amount of time for a white balance to complete.
    main()
