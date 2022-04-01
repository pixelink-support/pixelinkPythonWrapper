"""
jumboFrames.py

A demonstration of how to enable jumbo frames for a Gigabit Ethernet camera.

NOTE:
- All GigE cameras initialized after jumbo frames are enabled will use jumbo frames.
- All GigE cameras initialized after jumbo frames are disabled will not use jumbo frames.
- Support for jumbo frames is limited to the life of the application. i.e. You must enable it
  each time your program runs.
- Support for jumbo frames is limited to the life of the application enabling jumbo frames. i.e. If you have
  another program talking to a Pixelink GigE camera, that application must itself enable jumbo frames.
BE AWARE:
- The IEEE 802 standards committee does not official recognize jumbo frames.

- By "enabling" jumbo frames here, the Pixelink library is simply being asked to use jumbo frames. Your 
  network interface card (NIC) must not only support jumbo frames, but must also have jumbo frames enabled.

- NICs that do support jumbo frames typically default to jumbo frame support DISABLED. Please consult the 
  documentation for your NIC.

- All devices (routers, switches etc.) between the host NIC and the GigE camera must support and have 
  jumbo frames enabled.
"""

from pixelinkWrapper import*

PRIVATE_COMMAND_ENABLE_JUMBO_FRAMES = 37
PRIVATE_COMMAND_DISABLE_JUMBO_FRAMES = 38

"""
Enable or disable jumbo frame support in the Pixelink API.
"""
def enable_jumbo_frames(enable):

    hCamera = None
    opcode = [PRIVATE_COMMAND_ENABLE_JUMBO_FRAMES] if enable == True else PRIVATE_COMMAND_DISABLE_JUMBO_FRAMES
    ret = PxLApi.privateCmd(hCamera, opcode)
    return ret


def main():

    # Enable jumbo frames before we connect to any GigE cameras
    ret = enable_jumbo_frames(True)
    if not PxLApi.apiSuccess(ret[0]):
        print("ERROR: Unable to enable jumbo frames. Error code %d." % ret[0])
        return 1

    # And now any GigE cameras initialized after this will use jumbo frames.
	# Just connecting to a camera (any camera) 
    ret = PxLApi.initialize(0)
    if not PxLApi.apiSuccess(ret[0]):
        print("ERROR: Unable to initialize a camera. Error code %d." % ret[0])
        return 1

    hCamera = ret[1]

    # Do camera stuff

    PxLApi.uninitialize(hCamera)
    return 0


if __name__ == "__main__":
    main()