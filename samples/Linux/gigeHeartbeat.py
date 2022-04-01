"""
gigeHeartbeat.py

As required by the GigE Vision specification, Pixelink GigE cameras use a 'heartbeat'
between the camera and the host to determine the 'liveness' of the connection. If
no communication (normal camera interaction, or heartbeat) occurs within a certain
amount of time, the camera deems the connection as broken, and any further interaction
(except for connections) is refused.

This poses a problem when debugging because the debugger (e.g. Visual Studio, WinDbg)
will suspend all the threads in a debugee process (i.e. your program which is trying
to interact with the camera) for various reasons (e.g. breakpoints, exceptions, ...),
thereby disabling the background heartbeat mechanism, and thereby causing a connection
to a GigE camera to be terminated by the camera.

Simply put: debugging a program talking to a Pixelink GigE camera will have problems
after hitting a breakpoint or single-stepping.

The only way to improve this situation is to increase the heartbeat timeout. The
current default is 500ms, but this can currently be increased to as much as 65.535
seconds. A gigeHeartbeat demo application, demonstrates how to use the Pixelink API to 
do this.

All processes will start by using the default heartbeat timeout. If the heartbeat
timeout value is changed programmatically, the heartbeat timeout value is valid only
for the current process, and only for the life of the current process. 

The ability to change the heartbeat timeout is a double-edged sword. If you abruptly
end your debugging session without giving the Pixelink API a chance to close the
connection (i.e. PxLApi.uninitialize), the camera will not allow connections until 
the timeout from the last heartbeat passes. For example, if you set the heartbeat to
30 seconds, and then while debugging terminate debugging (e.g. in Visual Studio,
using Debug\Stop Debugging), without having called PxLApi.uninitialize, it may take 
up to 30 seconds before the camera will accept new connections.
"""

from pixelinkWrapper import*
import sys

# Commands for PxLApi.privateCmd
PRIVATE_COMMAND_SET_HEARTBEAT_TIMEOUT = 40

"""
Before connecting to a camera, set the GigE heartbeat timeout
so that we can debug this process without killing the connection.

We'll only do this for Debug runs.
"""
def initialize_camera(serialNumber):

    debugRun = sys.gettrace()
    if debugRun:
        
        # Before connecting to a GigE camera, set the GigE heartbeat timeout.
	    # It is recommended that you do this just before calling PxLApi.initialize.

        data = [PRIVATE_COMMAND_SET_HEARTBEAT_TIMEOUT, 65535]   # Set to max currently supported value (65535 ms = 65.535 seconds)
        
        ret = PxLApi.privateCmd(0, data)    # camera handle doesn't matter
        if not PxLApi.apiSuccess(ret[0]):
            return ret
    
    # Can now connect in the usual way to the GigE camera.
    return PxLApi.initialize(serialNumber)


def main():

    ret = initialize_camera(0)
    if not PxLApi.apiSuccess(ret[0]):
        print("ERROR: Unable to initialize a camera (Return code  = %d)" % ret[0])
        return 1

    hCamera = ret[1]

	# Interact with your GigE camera as usual

    # And now uninitialize in the usual way.
    PxLApi.uninitialize(hCamera)
    hCamera = 0

    return 0


if __name__ == "__main__":
    main()