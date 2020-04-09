"""
getCameraFeature.py

Demonstrates how to get some information about a camera feature.

Note that there are two places to get information about a feature:
1) getCameraFeatures
2) getFeature

getCameraFeatures can be used to query (generally) static information about 
a feature. e.g. number of parameters, if it's supported, param max min. etc.
 
getFeature is used to get the feature's current settings/value. 
(setFeature is used to set the feature's current settings/value.)
"""

from pixelinkWrapper import*


def decode_feature_flags(flags):
    if(flags & PxLApi.FeatureFlags.PRESENCE):
        print("Flag PRESENCE - feature is supported")
    if(flags & PxLApi.FeatureFlags.READ_ONLY):
        print("Flag READ_ONLY - feature can only be read")
    if(flags & PxLApi.FeatureFlags.DESC_SUPPORTED):
        print("Flag DESC_SUPPORTED - feature can be saved to different descriptors")
    if(flags & PxLApi.FeatureFlags.MANUAL):
        print("Flag MANUAL - feature controlled by external app")
    if(flags & PxLApi.FeatureFlags.AUTO):
        print("Flag AUTO - feature automatically controlled by camera")
    if(flags & PxLApi.FeatureFlags.ONEPUSH):
        print("Flag ONEPUSH - camera sets feature only once, then returns to manual operation")
    if(flags & PxLApi.FeatureFlags.OFF):
        print("Flag OFF - feature is set to last known state and cannot be controlled by app")

"""
Print information about an individual camera feature
"""
def print_camera_feature(feature):
    # Is the feature supported?
    isSupported = feature.uFlags & PxLApi.FeatureFlags.PRESENCE
    if(not(isSupported)):
        print("Feature {0} is not supported".format(feature.uFeatureId))
    else:
        print("Number of parameters: {0}".format(feature.uNumberOfParameters))
        print("Flags: {0}".format(feature.uFlags))
        decode_feature_flags(feature.uFlags)
        params = feature.Params
        for i in range(feature.uNumberOfParameters):
            print("Parameter {0}".format(i))
            print("Min value: {0}".format(params[i].fMaxValue))
            print("Max value: {0}".format(params[i].fMinValue))

"""
Print information about a feature.
 
This is one way to determine how many parameters are used by a feature.
The second way is demonstrated in print_feature_trigger.
The advantage of this method is that you can also see the max and min values
parameters supports.

Note that the max and min are exactly that: max and min.
It should not be assumed that all values between are supported.
For example, an ROI width parameter may have a min/max of 0/1600, but 
widths of 7, 13, 59 etc. are not supported.

Note too that a feature's min and max values may change as other 
features change.
For example, exposure and frame rate are interlinked, and changing
one may change the min/max for the other.

The feature flags reported by getCameraFeatures indicate which
flags are supported (e.g. FeatureFlags.AUTO). They do not indicate
the current settings; these are available through getFeature.
"""
def print_feature_parameter_info(hCamera, featureId):
    assert 0 != hCamera, "No initialized camera"
    print("\n----------Feature {0}----------\n".format(featureId))
    # Read information about a feature
    ret = PxLApi.getCameraFeatures(hCamera, featureId)
    if(PxLApi.apiSuccess(ret[0])):
        if(None != ret[1]):
            cameraFeatures = ret[1]
            assert 1 == cameraFeatures.uNumberOfFeatures, "Unexpected number of features"
            assert cameraFeatures.Features[0].uFeatureId == featureId, "Unexpected returned featureId"
            print_camera_feature(cameraFeatures.Features[0])

"""
In this case, what we'll do is demonstrate the use of FeatureId.ALL to read information
about all features at once.

However, we have to be careful because the order of the features is not 
such that we can just index into the array using the feature id value.
Rather, we have to explicitly search the array for the specific feature.
"""
def print_feature_parameter_info2(hCamera, featureId):
    assert 0 != hCamera, "No initialized camera"
    featureIndex = -1
    print("\n----------Feature {0}----------\n".format(featureId))
    # Read information about all features
    ret = PxLApi.getCameraFeatures(hCamera, PxLApi.FeatureId.ALL)
    if(PxLApi.apiSuccess(ret[0])):
        cameraFeatures = ret[1]
        assert 1 < cameraFeatures.uNumberOfFeatures, "Unexpected number of features"
        # Where in the structure of cameraFeatures is the feature we're interested in?
        for i in range(cameraFeatures.uNumberOfFeatures):
            if(featureId == cameraFeatures.Features[i].uFeatureId):
                featureIndex = cameraFeatures.Features[i].uFeatureId
                break
        # Did we find it?
        if(-1 == featureIndex):
            print("ERROR: Unable to find the information for feature {0}".format(featureId))
            return
        print_camera_feature(cameraFeatures.Features[featureIndex])

"""
Feature Shutter

FeatureId.SHUTTER is the exposure time.
"""
def print_feature_shutter(hCamera):
    assert 0 != hCamera, "No initialized camera"
    print("\n------------------------------")
    print("Print feature Shutter:\n")
    ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.SHUTTER)
    if(PxLApi.apiSuccess(ret[0])):
        flags = ret[1]
        params = ret[2]
        print("Exposure time: {0} seconds\n".format(params[0]))
        decode_feature_flags(flags)

"""
Feature White Balance

FeatureId.WHITE_BALANCE is not the RGB white balance, but rather the Color Temperature.
For the RGB white balance, see feature FeatureId.WHITE_SHADING.

Here we assume a colour camera.
If you're running this with a mono camera, getFeature will return an error.
"""
def print_feature_white_balance(hCamera):
    assert 0 != hCamera, "No initialized camera"
    print("\n------------------------------")
    print("Print feature White Balance:\n")
    ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.WHITE_BALANCE)
    if(PxLApi.apiSuccess(ret[0])):
        flags = ret[1]
        params = ret[2]
        print("Colour Temperature: {0} degrees Kelvin\n".format(params[0]))
        decode_feature_flags(flags)

"""
Feature Trigger

At this point in time FeatureId.TRIGGER has 5 parameters.
"""
def print_feature_trigger(hCamera):
    assert 0 != hCamera, "No initialized camera"
    print("\n------------------------------")
    print("Print feature Trigger:\n")
    ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.TRIGGER)
    if(PxLApi.apiSuccess(ret[0])):
        flags = ret[1]
        params = ret[2]
        assert PxLApi.TriggerParams.NUM_PARAMS == len(params), "Returned Trigger params number is different"
        print("Mode = {0}".format(params[PxLApi.TriggerParams.MODE]))
        print("Type = {0} {1}".format(params[PxLApi.TriggerParams.TYPE],
                                    decode_trigger_type(params[PxLApi.TriggerParams.TYPE])))
        print("Polarity = {0} {1}".format(params[PxLApi.TriggerParams.POLARITY],
                                     decode_polarity(params[PxLApi.TriggerParams.POLARITY])))
        print("Delay = {0}".format(params[PxLApi.TriggerParams.DELAY]))
        print("Parameter = {0}\n".format(params[PxLApi.TriggerParams.PARAMETER]))
        decode_feature_flags(flags)


def decode_trigger_type(triggerType):
    switcher = {
        PxLApi.TriggerTypes.FREE_RUNNING: "trigger type FREE_RUNNING",
        PxLApi.TriggerTypes.SOFTWARE: "trigger type SOFTWARE",
        PxLApi.TriggerTypes.HARDWARE: "trigger type HARDWARE"
        }
    return switcher.get(triggerType, "Unknown trigger type")


def decode_polarity(polarity):
    switcher = {
        0: "negative polarity",
        1: "positive polarity"
        }
    return switcher.get(polarity, "Unknown polarity")

"""
Feature GPIO

At this point in time we assume that GPIO has 6 parameters.

An error will be reported if you're using a microscopy camera
because they don't support GPIO.
"""
def print_feature_gpio(hCamera):
    assert 0 != hCamera, "No initialized camera"
    print("\n------------------------------")
    print("Print feature GPIO:\n")
    # Get information about GPO1 by setting params[0] == 1
    params = [1]
    ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.GPIO, params)
    if(PxLApi.apiSuccess(ret[0])):
        flags = ret[1]
        params = ret[2]
        assert PxLApi.GpioParams.NUM_PARAMS == len(params), "Returned GPIO params number is different"
        print("GpioNumber = {0}".format(params[PxLApi.GpioParams.INDEX]))
        print("Mode = {0}".format(params[PxLApi.GpioParams.MODE]))
        print("Polarity = {0} {1}".format(params[PxLApi.GpioParams.POLARITY],
                                        decode_polarity(params[PxLApi.GpioParams.POLARITY])))
        decode_feature_flags(flags)

"""
Feature Saturation

Again we assume that this is a color camera.
getFeature will return an error if the camera is a mono camera.
"""
def print_feature_saturation(hCamera):
    assert 0 != hCamera, "No initialized camera"
    print("\n------------------------------")
    print("Print feature Saturation:\n")
    ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.SATURATION)
    if(PxLApi.apiSuccess(ret[0])):
        flags = ret[1]
        params = ret[2]
        assert 1 == len(params), "Returned params number is different"
        print("Saturation = {0}".format(params[0]))
        decode_feature_flags(flags)


def main():
    # We assume there's only one camera connected
    ret = PxLApi.initialize(0)
    
    if(PxLApi.apiSuccess(ret[0])):
        hCamera = ret[1]

        # Print some information about the camera
        print_feature_parameter_info(hCamera, PxLApi.FeatureId.SHUTTER)
        print_feature_shutter(hCamera)
       
        print_feature_parameter_info(hCamera, PxLApi.FeatureId.WHITE_BALANCE)
        print_feature_white_balance(hCamera)
       
        print_feature_parameter_info(hCamera, PxLApi.FeatureId.TRIGGER)
        print_feature_trigger(hCamera)

        print_feature_parameter_info(hCamera, PxLApi.FeatureId.GPIO)
        print_feature_gpio(hCamera)

        print_feature_parameter_info(hCamera, PxLApi.FeatureId.SATURATION)
        print_feature_saturation(hCamera)

        # Demonstrate two ways to get the same information
        print_feature_parameter_info(hCamera, PxLApi.FeatureId.ROI)
        print_feature_parameter_info2(hCamera, PxLApi.FeatureId.ROI)
        
        # Uninitialize the camera now that we're done with it.
        PxLApi.uninitialize(hCamera)
        return 0
    else:
        print("ERROR: {0}\n".format(ret[0]))
        return 1


if __name__ == "__main__":
    main()
