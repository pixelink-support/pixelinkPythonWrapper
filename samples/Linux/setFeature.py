
"""
setFeature.py

Simple sample application demostrating the use of the setFeature
function in the pixelinkWrapper
"""

from pixelinkWrapper import*

"""
Demostrate the setFeature function of the pixelinkWrapper, by setting
FeatuerId.ROI. It also uses getCameraFeatures to demostrate how to
determine feature limits
"""
def main():
    
    #
    # Step 1
    #     Grab a Pixelink camera. Note that if there is more than one camera
    #     connected, this will just grab the first one found. If we wanted 
    #     a specific camera, than we could use getNumberCameras/initialize
    ret = PxLApi.initialize(0)
    if not PxLApi.apiSuccess(ret[0]):
      print ("  Could not find a camera!")
      return

    hCamera = ret[1]

    # 
    # Step 2
    #     Call getCameraFeatures for FeatuerId.ROI. We do this so we can determine 
    #     the ROI limits. Like all pixelinkWrapper functions, getCameraFeatures 
    #     returns a tuple with number of elements. More specifically, 
    #     getCameraFeatures will return:
    #         ret[0] - Return code
    #         ret[1] - A list of features. Given that we are requesting on a specific
    #                  feature, there should only be one element in this list
    ret = PxLApi.getCameraFeatures(hCamera, PxLApi.FeatureId.ROI)
    if not PxLApi.apiSuccess(ret[0]):
      print ("  Could not getCameraFeatuers on ROI, ret: %d!" % ret[0])
      PxLApi.uninitialize(hCamera)
      return

    cameraFeatures = ret[1]
    assert 1 == cameraFeatures.uNumberOfFeatures
    maxWidth  = cameraFeatures.Features[0].Params[PxLApi.RoiParams.WIDTH].fMaxValue
    maxHeight = cameraFeatures.Features[0].Params[PxLApi.RoiParams.HEIGHT].fMaxValue
    print ("  This camera has a max ROI of %d x %d" % (maxWidth, maxHeight))

    # 
    # Step 3
    #     Call setFeature for FeatuerId.ROI.  
    #     We will set the ROI to be half of the max, rougly centered
    params = []
    params.insert (PxLApi.RoiParams.WIDTH, maxWidth / 2)
    params.insert (PxLApi.RoiParams.HEIGHT, maxHeight / 2)
    params.insert (PxLApi.RoiParams.LEFT, maxWidth / 4)
    params.insert (PxLApi.RoiParams.TOP, maxHeight / 4)

    ret = PxLApi.setFeature(hCamera, PxLApi.FeatureId.ROI, PxLApi.FeatureFlags.MANUAL, params)
    if not PxLApi.apiSuccess(ret[0]):
      print ("  Could not setFeature on ROI, ret: %d!" % ret[0])
      PxLApi.uninitialize(hCamera)
      return

    # 
    # Step 4
    #     Read back the ROI, as the camera may have had to adjust the ROI slightly
    #     to accomodate sensor restrictions
    roundingRequired = PxLApi.ReturnCode.ApiSuccessParametersChanged == ret[0]

    #     Call getFeature. Like all pixelinkWrapper functions, getFeature 
    #     returns a tuple with number of elements. More specifically, 
    #     getFeature will return:
    #         ret[0] - Return code
    #         ret[1] - A bit mask of PxLApi.FeatureFlags
    #         ret[2] - A list of paramters. The number of elements in the list varies
    #                  with the feature
    ret = PxLApi.getFeature (hCamera, PxLApi.FeatureId.ROI)
    if PxLApi.apiSuccess(ret[0]):
      flags = ret[1]
      updatedParams = ret[2]
      print ("  Cameras ROI set to %d x %d (%d, %d)" %     \
             (updatedParams[PxLApi.RoiParams.WIDTH],         \
              updatedParams[PxLApi.RoiParams.HEIGHT],        \
              updatedParams[PxLApi.RoiParams.LEFT],          \
              updatedParams[PxLApi.RoiParams.TOP]))

      if roundingRequired:
        print (  "  Warning -- The camera had to make a small adjustment to the ROI")

    # 
    # Step 5
    #     Release the camera
    PxLApi.uninitialize(hCamera)


if __name__ == "__main__":
    main()

