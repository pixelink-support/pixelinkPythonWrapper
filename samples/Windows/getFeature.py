"""
getFeature.py

Simple sample application demostrating the use of the getFeature function 
in the pixelinkWrapper.
"""

from pixelinkWrapper import*

"""
Demostrate the getFeature function of the pixelinkWrapper, by getting
FeatureId.TRIGGER, as this is one of the more 'sophisticatted' features
"""
def main():

    #
    # Step 1
    #     Grab a Pixelink camera. Note that if there is more than one camera
    #     connected, this will just grab the first one found. If we wanted
    #     a specific camera, than we could use getNumberCameras/initialize
    # 
    #     Note also, we chose to use the optional InitializeExFlags.MONITOR_ACCESS_ONLY flag.  
    #     Pixelink GigE cameras can only have one application controlling the camera at any 
    #     time, so we use this falg to indicate that we don't intend to 'control' the camera, 
    #     we will just be reading camera settings
    ret = PxLApi.initialize(0, PxLApi.InitializeExFlags.MONITOR_ACCESS_ONLY)
    if not PxLApi.apiSuccess(ret[0]):
      print ("Could not find a camera!")
      return

    hCamera = ret[1]

    # 
    # Step 2
    #     Call getFeature. Like all pixelinkWrapper functions, getFeature 
    #     returns a tuple with number of elements. More specifically, 
    #     getFeature will return:
    #         ret[0] - Return code
    #         ret[1] - A bit mask of PxLApi.FeatureFlags
    #         ret[2] - A list of paramters. The number of elements in the list varies
    #                  with the feature
    ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.TRIGGER)
    if PxLApi.apiSuccess(ret[0]):
      flags = ret[1]
      params = ret[2]

      # 
      # Step 3
      #     Interpret the resuts
      print("Camera Trigger:")
      if not flags & PxLApi.FeatureFlags.PRESENCE:
        print ("        State: NOT SUPPORTED")
      else:
        state = 'DISABLED'   if flags & PxLApi.FeatureFlags.OFF else      \
                'CONTINUOUS' if flags & PxLApi.FeatureFlags.AUTO else      \
                'ONE_TIME'   if flags & PxLApi.FeatureFlags.ONEPUSH  else  \
                'MANUAL'
        type = 'HARDWARE' if params[1] == PxLApi.TriggerTypes.HARDWARE else \
               'SOFTWARE' if params[1] == PxLApi.TriggerTypes.SOFTWARE else \
               'ACTION'
        print ("        State: %s" % state)
        print ("         Type: %s" % type)
        if params[PxLApi.TriggerParams.MODE] == PxLApi.TriggerModes.MODE_0:
          print ("  Description: Trigger a single frame, using current exposure")
        elif params[PxLApi.TriggerParams.MODE] == PxLApi.TriggerModes.MODE_1:
          print ("  Description: Trigger a single frame, trigger duration defines exposure")
        elif params[PxLApi.TriggerParams.MODE] == PxLApi.TriggerModes.MODE_14:
          numFrames = params[PxLApi.TriggerParams.NUMBER]
          if numFrames == 0:
            print ("  Description: Trigger frames until a StreamStop is issued")
          else:
            print ("  Description: Trigger %d frames, using current exposure" % numFrames)
        else:
            print ("  Description: Trigger mode %d" % params[PxLApi.TriggerParams.MODE])

    else:
      print ("getFeature return code: %d" % ret[0])
    
    # 
    # Step 4
    #     Release the camera
    PxLApi.uninitialize(hCamera)


if __name__ == "__main__":
    main()
