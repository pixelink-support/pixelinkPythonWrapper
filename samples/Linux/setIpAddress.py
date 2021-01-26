"""
setIpAddress.py 

This demonstration application assumes that you have one GigE camera visible to the host, and that
that GigE camera is connected to a GigE card with a statically assigned IP address.

This demo app is incomplete in that we can't know a priori what IP address, subnet mask and 
gateway *YOU* need to set. If you're unsure what values these need to be, please consult 
your local network administrator/administratrix.
"""

from pixelinkWrapper import*

A_OK = 0            # non-zero error codes
GENERAL_ERROR = 1

"""
Check if an IP address matches the network interface card (NIC) subnet
"""
def is_subnet_matches(cameraIpAddress, cameraSubnetMask, cameraIdInfo):
    
    cameraSubnetAddress = list()
    nicSubnetAddress = list()
    for i in range(len(cameraIpAddress)):
        cameraSubnetAddress.append(cameraIpAddress[i] & cameraSubnetMask[i])

    for i in range(len(cameraIdInfo.NicIpAddress.Address.u8Address)):
        nicSubnetAddress.append(cameraIdInfo.NicIpAddress.Address.u8Address[i] & cameraIdInfo.NicIpMask.Address.u8Address[i])

    for i in range(len(cameraIpAddress)):
        if cameraSubnetAddress[i] != nicSubnetAddress[i]:
            return False
    
    return True

def main():

    # *******************  NOTE: Assign your values here *******************
    cameraIpAddress  =     (192, 168, 1, 2)
    cameraSubnetMask =	   (255, 255, 255, 0)
    cameraDefaultGateway = (222, 1, 1, 1)
    addressIsPersistent =  False
	# *******************   NOTE: Assign your values here  *******************

    # Remove this after you've set up your own appropriate values above.
    print("This demonstration application has not been configured for your local environment\nSee the notes in setIpAddress.py for more information.")
    return GENERAL_ERROR

    # Check our assumption that there's only one camera
    ret = PxLApi.getNumberCameras()
    numberOfCameras = ret[1]
    
    assert PxLApi.apiSuccess(ret[0])
    assert 1 == len(numberOfCameras)
    
    # Get the information for that camera
    cameraIdInfo = numberOfCameras[0]

    # A bit of sanity checking
    assert cameraIdInfo.NicIpAddress.Address.u32Address != 0

    if not is_subnet_matches(cameraIpAddress, cameraSubnetMask, cameraIdInfo):
        print("WARNING: You are setting an IP address that doesn't match the network interface card (NIC) subnet")

    # Copy MAC address found in the cameraIdInfo into a list
    cameraMacAddress = list()
    for i in range(len(cameraIdInfo.CameraMac.MacAddr)):
        cameraMacAddress.append(cameraIdInfo.CameraMac.MacAddr[i])

    ret = PxLApi.setCameraIpAddress(cameraMacAddress, cameraIpAddress, cameraSubnetMask, cameraDefaultGateway, addressIsPersistent)

    print("PxLApi.setCameraIpAddress returned %d" % ret[0])
    if not PxLApi.apiSuccess(ret[0]):
        return GENERAL_ERROR

    return A_OK


if __name__ == "__main__":
    main()
