"""
slowMotionVideo.py

This demonstrates how to create videos using the Pixelink API. Specifically, 
this applocation will create videos that play back normal motion, to slow motion.

This application showcases how to use:
    - PxLApi.getEncodedClip 
    - PxLApi.formatClip

NOTE: This application assumes there is at most, one Pixelink camera connected to the system

This application is intended to work with very high frame rates. That is the camera is 
outputting image data at a very high rate. For most systems we will need to do more 
compression to accomodate this high capture data rate. This takes more procssing power 
to do the compression, but on most systems, it's the disk access that dictates our ability 
to sink image data at high data rates. So, we reduce the bitrate (and quality) to do more 
compression, so that we are less likely to loose capture data.
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
DEFAULT_RECORD_DURATION = 20    # in seconds
CLIP_PLAYBACK_BITRATE = int(PxLApi.ClipPlaybackDefaults.BITRATE_DEFAULT/3)


def get_parameters():

    # Let the app know the user parameters. 
    global recordTime
    global bitRate
    global frameRate
    global fileName

    # Step 1
    # Simple parameter check
    # Note: Must have at least the fileName; Only 3 options allowed
    #       2 > len(sys.argv) - No play time specified; use the default
    #       8 < len(sys.argv) - User specifies the play time
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
        elif "-b" == sys.argv[i] or "-B" == sys.argv[i]:
            if i+1 >= len(sys.argv):
                return GENERAL_ERROR
            parm = int(sys.argv[i+1])
            if parm < 1000:
                return GENERAL_ERROR
            bitRate = parm
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

    print("\n This application will capture video for the sepcified number of seconds. If the camera's frame\n"
          " rate is playback_framerate, then the generated (a .avi file) will play back at 'normal speed'.\n"
          " However, this application allows you to create 'slow motion' videos by setting the camera up so\n"
          " that it uses frame rates that are higher than playback_framerate. In so doing, you can create\n"
          " very 'dramatic' slow motion videos, especially when using a very high camera frame rates, \n"
          " several hundred fps or more. Note however, that very high frame rates are only possible with\n"
          " very short exposure times, which (generally) require a lot of light. In addition to adjusting\n"
          " your lighting accordingly, consider using the following strategies to facilitate very high frame\n"
          " rates:")
    print("    - Adding Pixel Addressing. Binning in particular will accomodate faster frame rates\n"
          "      and help 'brighten' dark images\n"
          "    - Adding Gain to brighten the images\n"
          "    - Reducing the ROI to accomodate faster frame rates\n")
    print("    Usage: python slowMotionVideo.py [-t capture_duration] [-b playback_bitrate] [-f playback_framerate] video_name\n"
          "       where:\n"
          "          -t capture_duration   How much time to spend capturing video (in seconds).")
    print("                                If not specified, %i seconds of video will be used." % DEFAULT_RECORD_DURATION)
    print("          -b playback_bitrate   Bitrate (b/s) that will be used for playback. This value\n"
          "                                provides guidance on how much compression to use. More\n"
          "                                compression means lower quality. Generally, if the video\n"
          "                                capture cannot keep pace with the cameras stream (as indicated\n"
          "                                by this application issuing a warning), then you will want to")
    print("                                lower this value. Its default value is %i" % CLIP_PLAYBACK_BITRATE)
    print("          -f playback_framerate Framerate (f/s) that will be used for playback. This value\n"
          "                                determines the duration of the clip. If this value matches\n"
          "                                the camera's framerate, then the playback duration will")
    print("                                match the capture_duration. Its default value is %i" % DEFAULT_PLAYBACK_FRAME_RATE)
    print("          video_name            Name of file to generate (it will be postfixed with .avi)\n")
    print("    Example:")
    print("        python slowMotionVideo.py -t 30 clip")
    print("              This will capture a video, called clip.avi, that records for about 30 seconds.")

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
    if cameraFps < frameRate:
        # Although this will 'work', such a configuration will create a fast motion video,
        # and a rather poor quality one at that. For these instances, you should be using
        # the demo FastMotionVideo
        print(" Error:  The camera's frame rate is currently %.2f; it should be > %.2f." % (cameraFps, frameRate))
        PxLApi.uninitialize(hCamera)
        return GENERAL_ERROR

    numImages = int(recordTime * cameraFps)
    ret = PxLApi.setStreamState(hCamera, PxLApi.StreamState.START)
    if not PxLApi.apiSuccess(ret[0]):
        print(" Error: Could not start the stream.")
        PxLApi.uninitialize(hCamera)
        return GENERAL_ERROR

    # Step 4
    # Create a folder for a clip if it does not exist
    if not os.path.exists("slowMotionVideo"):
        os.makedirs("slowMotionVideo")
    # Start capturing the required images into the clip
    h264File = "slowMotionVideo/" + fileName + ".h264"

    clipInfo = PxLApi.ClipEncodingInfo()
    clipInfo.uStreamEncoding = PxLApi.ClipEncodingFormat.H264
    clipInfo.uDecimationFactor = 1 # No decimation
    clipInfo.playbackFrameRate = frameRate
    clipInfo.playbackBitRate = bitRate

    print(" Recording %i seconds of h264 compressed video (based on %i images). Press any key to abort...\n"
          % (recordTime, numImages))

    ret = PxLApi.getEncodedClip(hCamera, numImages, h264File, clipInfo, term_fn_get_encoded_clip)
    if PxLApi.apiSuccess(ret[0]):
        
        global captureFinished
        while not captureFinished:
            if msvcrt.kbhit():
                # User wants to abort. Tell the API to abort the capture by stopping the stream. This should call our callback with
                # an error.
                PxLApi.setStreamState(hCamera, PxLApi.StreamState.STOP)
            else:
                # No need to steal a bunch of cpu cycles on a loop doing nothing -- sleep for a bit until it's time to check for keyboard
                # input again.
                time.sleep(0.5)

    PxLApi.setStreamState(hCamera, PxLApi.StreamState.STOP) # already stopped if user aborted, but that's OK

    # Step 5
    # Clip capture is done. If it completed OK, create the clip video file (.avi)
    if PxLApi.apiSuccess(ret[0]):
        if PxLApi.apiSuccess(captureRc):
            if PxLApi.ReturnCode.ApiSuccessWithFrameLoss == captureRc:
                print("Warning\n %i images had to be streamed to capture %i of them." % (numImagesStreamed, numImages))
            else:
                print("Success\n %i images captured." % numImages)

            # Step 6
            # Convert the clip capture file, into a .avi video file
            aviFile = "slowMotionVideo/" + fileName + ".avi"
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
    bitRate = CLIP_PLAYBACK_BITRATE
    frameRate = DEFAULT_PLAYBACK_FRAME_RATE
    fileName = None
    # 'Globals' shared between our main line, and the clip callback
    numImagesStreamed = 0
    captureRc = PxLApi.ReturnCode.ApiSuccess
    captureFinished = False
    main()
