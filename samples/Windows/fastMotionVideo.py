"""
fastMotionVideo.py

This demonstrates how to create videos using the Pixelink API. Specifically, 
this applocation will create videos that play back normal motion, to fast motion.

This application showcases how to use:
    - PxLApi.getEncodedClip 
    - PxLApi.formatClip

NOTE: This application assumes there is at most, one Pixelink camera connected to the system
"""

from pixelinkWrapper import*
import sys
import os
import time
import msvcrt

# A few useful constants.
A_OK = 0            # non-zero error codes
GENERAL_ERROR = 1

DEFAULT_PLAYBACK_FRAME_RATE = 25    # in frames/second.  25 == smooth(ish) video
DEFAULT_RECORD_DURATION = 5 * 60    # in seconds
DEFAULT_CLIP_DECIMATION = 5         # Every X'th frame will be included in the clip


def get_parameters():

    # Let the app know the user parameters. 
    global recordTime
    global decimation
    global frameRate
    global fileName

    # Step 1
    # Simple parameter check
    # Note: Must have at least the fileName; Only 3 options allowed
    if 2 > len(sys.argv) or 8 < len(sys.argv):   
            print("\nERROR -- Incorrect number of parameters")
            return GENERAL_ERROR

    # Step 2
    # Parse the command line looking for the optional parameters.
    for i in range(1, len(sys.argv)-1, 2):
        if "-t" == sys.argv[i] or "-T" == sys.argv[i]:
            if i+1 >= len(sys.argv):
                return GENERAL_ERROR
            parm = int(sys.argv[i+1])
            if parm < 1:
                return GENERAL_ERROR
            recordTime = parm
        elif "-d" == sys.argv[i] or "-D" == sys.argv[i]:
            if i+1 >= len(sys.argv):
                return GENERAL_ERROR
            parm = int(sys.argv[i+1])
            if parm < 1:
                return GENERAL_ERROR
            decimation = parm
        elif "-f" == sys.argv[i] or "-F" == sys.argv[i]:
            if i+1 >= len(sys.argv):
                return GENERAL_ERROR
            parm = int(sys.argv[i+1])
            if parm < 1:
                return GENERAL_ERROR
            frameRate = parm
        else:
            return GENERAL_ERROR

    # Step 3
    # The last parameter must be the file name
    if '-' == sys.argv[len(sys.argv)-1]:
        return GENERAL_ERROR
    fileName = sys.argv[len(sys.argv)-1]

    return A_OK

"""
Returns the frame rate being used by the camera. Ideally, this is simply PxLApi.FeatureId.ACTUAL_FRAME_RATE,
but some older cameras do not support that. If that is the case, use PxLApi.FeatureId.FRAME_RATE, which is 
always supported.
"""
def effective_frame_rate(hCamera):

    frameRateFeature = PxLApi.FeatureId.FRAME_RATE

    # Step 1
    # Determine if the camera supports PxLApi.FeatureId.ACTUAL_FRAME_RATE
    ret = PxLApi.getCameraFeatures(hCamera, PxLApi.FeatureId.ACTUAL_FRAME_RATE)
    if PxLApi.apiSuccess(ret[0]):
        # Step 2
        # Get the 'best available' frame rate of the camera
        cameraFeatures = ret[1]
        if cameraFeatures.Features[0].uFlags & PxLApi.FeatureFlags.PRESENCE:
            frameRateFeature = PxLApi.FeatureId.ACTUAL_FRAME_RATE
        
    ret = PxLApi.getFeature(hCamera, frameRateFeature)
    assert PxLApi.apiSuccess(ret[0])
    params = ret[2]
    frameRate = params[0]

    return frameRate


def usage():

    print("\n This application will capture a 'fast motion' video clip. More specificaly, over the capture period\n"
          " it will create a video clip using every N'th frame from the stream (thus creating the fast motion effect).\n"
          "    Usage: python fastMotionVideo.py [-t capture_duration] [-d decimation] [-f playback_framerate] capture_names\n"
          "       where:\n"
          "          -t capture_duration   How much time to spend captureing video (in seconds).")
    print("                                If not specified, %i seconds of video will be captured." % DEFAULT_RECORD_DURATION)
    print("          -d decimation         Only include every N'th image from the camera stream, \n"
          "                                in the video. The larger this number, the faster the")
    print("                                video appears. Its default value is %i seconds." % DEFAULT_CLIP_DECIMATION)
    print("          -f playback_framerate Framerate (f/s) that will be used for playback. This value\n"
          "                                determines the duration of the clip. If this value matches\n"
          "                                the camera's framerate, then the playback duration will ")
    print("                                match the capture_duration. Its default value is %i" % DEFAULT_PLAYBACK_FRAME_RATE)
    print("          capture_names         Names used for the captured files. The video will have\n"
          "                                a '.avi' extension.\n")
    print("    Example:")
    print("        python fastMotionVideo.py -t 30 cap")
    print("              Over a 30 second period, a video will be captured using every 5th image, so that")
    print("              resulting clip will be %i seconds long (assuming 25 fps).\n" % (30 / DEFAULT_CLIP_DECIMATION))

"""
Function that's called when PxLApi.getEncodedClip is finished capturing frames, or can't continue
capturing frames.
"""
@PxLApi._terminationFunction
def term_fn_get_encoded_clip(hCamera, numberOfFrameBlocksStreamed, retCode):
    # Just record the capture information into our shared (global) varaibles so the main line
    # can report/take action on the result.
    global numImagesStreamed
    global captureRc
    global captureFinished
    numImagesStreamed = numberOfFrameBlocksStreamed
    captureRc = retCode
    captureFinished = True
    return PxLApi.ReturnCode.ApiSuccess


def main():

    # Step 1
    # Validate the user parameters, getting user specified (or default) values
    if A_OK != get_parameters():
        usage()
        return GENERAL_ERROR

    # Step 2
    # Grab our camera
    ret = PxLApi.getNumberCameras()
    
    if PxLApi.apiSuccess(ret[0]):
        cameraIdInfo = ret[1]
        if 1 != len(cameraIdInfo):
            print(" Error: There should be exactly one Pixelink camera connected.")
            return GENERAL_ERROR
    else:
        print(" Error: Could not find connected camera(s).")
        return GENERAL_ERROR

    ret = PxLApi.initialize(0)
    if not PxLApi.apiSuccess(ret[0]):
        print(" Error: Could not initialize the camera.")
        return GENERAL_ERROR

    hCamera = ret[1]

    # Step 3
    # Determine the effective frame rate for the camera, and the number of images we will need to
    # capture the video of the requested length then start the stream
    cameraFps = effective_frame_rate(hCamera)
    numImages = recordTime * cameraFps
    numImages = int(numImages / decimation) # Include the decimation factor
    ret = PxLApi.setStreamState(hCamera, PxLApi.StreamState.START)
    if not PxLApi.apiSuccess(ret[0]):
        print(" Error: Could not start the stream.")
        PxLApi.uninitialize(hCamera)
        return GENERAL_ERROR

    # Step 4
    # Create a folder for a clip if it does not exist 
    if not os.path.exists("fastMotionVideo"):
        os.makedirs("fastMotionVideo")
    # Start capturing the required images into the clip
    h264File = "fastMotionVideo/" + fileName + ".h264"
    
    clipInfo = PxLApi.ClipEncodingInfo()
    clipInfo.uStreamEncoding = PxLApi.ClipEncodingFormat.H264
    clipInfo.uDecimationFactor = decimation
    clipInfo.playbackFrameRate = frameRate
    clipInfo.playbackBitRate = PxLApi.ClipPlaybackDefaults.BITRATE_DEFAULT
    print(" Recording %i seconds of h264 compressed video (based on %i images)."
          % (recordTime, numImages))
    print(" Press any key to abort...\n")
    ret = PxLApi.getEncodedClip(hCamera, numImages, h264File, clipInfo, term_fn_get_encoded_clip)
    if PxLApi.apiSuccess(ret[0]):
        
        # Step 5
        # Check whether any key has been pressed to abort
        global captureFinished
        while not captureFinished:
            if msvcrt.kbhit():
                # User wants to abort. Tell the API to abort the capture by stopping the stream. This should call our callback with
                # an error.
                PxLApi.setStreamState(hCamera, PxLApi.StreamState.STOP)
            else:
                # No need to steal a bunch of cpu cycles on a loop doing nothing -- sleep for a bit until it's time to check for keyboard
                # input again.
                time.sleep(0.2)

    PxLApi.setStreamState(hCamera, PxLApi.StreamState.STOP) # already stopped if user aborted, but that's OK

    # Step 6
    # Clip capture is done.  If it completed OK, create the clip video file (.avi)
    if PxLApi.apiSuccess(ret[0]):
        if PxLApi.apiSuccess(captureRc):
            if PxLApi.ReturnCode.ApiSuccessWithFrameLoss == captureRc:
                print("Warning\n %i images had to be streamed to capture %i of them." % (numImagesStreamed, numImages))
            else:
                print("Success\n %i images captured." % numImages)

            # Step 7
            # Convert the clip capture file, into a .avi video file
            aviFile = "fastMotionVideo/" + fileName + ".avi"
            ret = PxLApi.formatClip(h264File, aviFile, PxLApi.ClipEncodingFormat.H264, PxLApi.ClipFileContainerFormat.AVI)
        else:
            ret = [captureRc,]

    if not PxLApi.apiSuccess(ret[0]):
        print("Error\n PxLApi.getEncodedClip/PxLApi.formatClip returned %i" % ret[0])

    PxLApi.uninitialize(hCamera)

    return ret[0]


if __name__ == "__main__":
    # Default global recording parameters
    recordTime = DEFAULT_RECORD_DURATION
    decimation = DEFAULT_CLIP_DECIMATION
    frameRate = DEFAULT_PLAYBACK_FRAME_RATE
    fileName = None
    # 'Globals' shared between our main line, and the clip callback
    numImagesStreamed = 0
    captureRc = PxLApi.ReturnCode.ApiSuccess
    captureFinished = False
    main()
