"""
lowUsbMemory.py

Demonstrates how to detect / deal with systems configured with a small amount of USB 
memory.

As per the INSTALL.INSTRUCTIONS.txt file that accompanies the Pixelink SDK, by default, 
many Linux systems may not be configured with enough USB buffer memory to permit optimal 
streaming for a high performance USB3 camera, such as many models of the Pixelink cameras. 
This same TXT file offers advice on how you may reconfigure your system to allocate more 
USB buffer memory.

However, should you choose not to re-configure your system, you can use the Pixelink Python 
wrapper function 'PxLApi.setStreamState' to determine if your system's USB memory requirements 
are less than optimal. In particular, if the PxLApi.setStreamState returns a response code of 
'PxLApi.ReturnCode.ApiSucessLowMemory' when you attempt a PxLApi.StreamState.START or 
PxLApi.StreamState.PAUSE operation, then the Pixelink API has detected that your systems USB 
memory allocation is sub-optimal. The Pixelink API has made some internal 'concessions' to 
accomodate. These concesions MAY result in some frame loss when the camera is streaming. More
on this below.

So, what should your application do when PxLApi.setStreamState returns 
'PxLApi.ReturnCode.ApiSuccessLowMemory'??
There are several otions:
 1. Do nothing.
       Meaning, the Pixelink API has already made some internal concessions
       to deal with the sub-optimal USB buffer space. If while streaming,
       your camera sontinually flashes its LED green -- then no frame loss
       os occuring. However, if you see a periodic red flash from the the
       camera, then you are experiencing some frame loss that is probably
       the result of these concessions. In which case, you may want to
       consider one of the other options
 2. Use a 8-bit pixel format (if you're not already).
       The 12 and 16-bit pixel formats (MONO16, MONO12_PACKED, and BAYER16)
       produce larger images that require more USB buffer memory
 3. Reduce the region of interest (ROI) to reduce image size.
 4. Use Pixel Addressing to reduce image size.
 5. Reduce the frame rate.

This sample, uses strategy #5 from above.
"""

from pixelinkWrapper import*


def main():

    currentFrameRate = 0.0
    minFrameRate = 0.0

    # We assume there's only one camera connected
    ret = PxLApi.initialize(0)
    if PxLApi.apiSuccess(ret[0]):
        hCamera = ret[1]

        ret = PxLApi.getCameraFeatures(hCamera, PxLApi.FeatureId.FRAME_RATE)
        if PxLApi.apiSuccess(ret[0]):
            cameraFeatures = ret[1]
            minFrameRate = cameraFeatures.Features[0].Params[0].fMinValue
            
            ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.FRAME_RATE)
            if not PxLApi.apiSuccess(ret[0]):
                print("Difficuty accessing PxLApi.FeatureId.FRAME_RATE, rc=%i" % ret[0])
                PxLApi.uninitialize(hCamera)
                return 1

            params = ret[2]
            currentFrameRate = params[0]

            ret = PxLApi.setStreamState(hCamera, PxLApi.StreamState.START)
            if not PxLApi.apiSuccess(ret[0]):
                print("Difficuty starting the stream, rc=%i" % ret[0])
                PxLApi.uninitialize(hCamera)
                return 1

            while PxLApi.ReturnCode.ApiSuccessLowMemory == ret[0]:
                print("Sub-optimal USB memory allocation detected at a frame rate of %5.2f fps" % currentFrameRate)
                if currentFrameRate == minFrameRate:
                    break # We cannot reduce the frame rate any lower.

                # try restarting the stream at a lower frame rate
                ret = PxLApi.setStreamState(hCamera, PxLApi.StreamState.STOP)
                if not PxLApi.apiSuccess(ret[0]):
                    break

                # reduce the frame rate by 20%, being careful to not go lower than the minimum value
                currentFrameRate = (currentFrameRate * 0.8)
                if minFrameRate > currentFrameRate:
                    currentFrameRate = minFrameRate
                params = [currentFrameRate,]
                ret = PxLApi.setFeature(hCamera, PxLApi.FeatureId.FRAME_RATE, PxLApi.FeatureFlags.MANUAL, params)
                if not PxLApi.apiSuccess(ret[0]):
                    break

                ret = PxLApi.setStreamState(hCamera, PxLApi.StreamState.START)
                if not PxLApi.apiSuccess(ret[0]):
                    break

            if PxLApi.apiSuccess(ret[0]):

                if PxLApi.ReturnCode.ApiSuccessLowMemory != ret[0]:
                    print("Camera can stream fine at a frame rate of %5.2f fps" % currentFrameRate)
                else:
                    print("Cannot fully accomodate sub-optimal USB memory allocations, "
                          "try adjusting ROI, PIXEL_ADDRESSING, or PIXEL_FORMAT")

            else:
                print("Difficuty accessing PxLApi.FeatureId.FRAME_RATE, rc=%i" % ret[0])

        PxLApi.setStreamState(hCamera, PxLApi.StreamState.STOP)
        PxLApi.uninitialize(hCamera)
    
    else:
        print("Could not Initialize the camera! rc=%i" % ret[0])
        return 1

    return 0


if __name__ == "__main__":
    main()
