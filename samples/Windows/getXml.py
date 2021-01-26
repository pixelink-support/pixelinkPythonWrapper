"""
getXml.py 

A simple demonstration of reading the XML file for a given camera
"""

from pixelinkWrapper import*

EXIT_SUCCESS = 0
EXIT_FAILURE = 1

def main():

    # Initialize any camera
    ret = PxLApi.initialize(0)
    if not PxLApi.apiSuccess(ret[0]):
        print("ERROR: Unable to initialize a camera (%d)" % ret[0])
        return EXIT_FAILURE

    hCamera = ret[1]

    # Grab the XML from the camera
    ret = PxLApi.getCameraXml(hCamera)
    if not PxLApi.apiSuccess(ret[0]):
        print("ERROR: Cannot read the XML file of this camera (%d)" % ret[0])
        PxLApi.uninitialize(hCamera)
        return EXIT_FAILURE

    xmlFile = ret[1]

    print("=================== Camera's XML file (%d bytes) ===================\n" % len(xmlFile))
    print("%s" % str(xmlFile, encoding='utf-8'), end='')

    PxLApi.uninitialize(hCamera)
    return EXIT_SUCCESS


if __name__ == "__main__":
    main()