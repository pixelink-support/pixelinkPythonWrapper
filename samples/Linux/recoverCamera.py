"""
recoverCamera.py

Demonstrates how to 'fully initialize' a camera.  That is, to connect to a camera in an 
unknown state, and to initialize the camera so that it is in a known, default state.

The techniques shown here are particularly useful if your applications crashes, or is shut 
down, without having to having done the necessary 'cleanup' operations.
"""

from pixelinkWrapper import*


def main():

    """
    Step 1.
	    Initialize the camera in a stream stopped state.  
	
        If a camera control application 'crashes' while stream a camera, then the 
	    camera is left in a state where it is trying to output images to the host, 
	    but the host is not in a state to receive images. This is characterized 
	    by the camera's LED flashing red. Under these circumstances, the USB host 
	    may have difficulties initializing the camera, and establishing a control
	    path to the camera.
	
        Under these circumstances, asserting a stream stop state at initialization, 
	    will ensure the camera control path gets properly established. Applications
	    may want to consider using PxLApi.InitializeExFlags.ISSUE_STREAM_STOP every 
	    time they initialize a camera, but keep in mind this may not have the desired
	    effect if you have multiple applications controlling the same camera.
    """

    # We assume there's only one camera connected
    ret = PxLApi.initialize(0, PxLApi.InitializeExFlags.ISSUE_STREAM_STOP)
    if PxLApi.apiSuccess(ret[0]):
        hCamera = ret[1]

        """
        Step 2.
	        Assert all camera features to the factory default values.  
	
            Rather than leave the camera parameters at their last used value, 
            set them to factory default values. 
        """

        ret = PxLApi.loadSettings(hCamera, PxLApi.Settings.SETTINGS_FACTORY)
        if not PxLApi.apiSuccess(ret[0]):
            print("Could not load factory settings!")
        else:
            print("Factory default settings restored")

        # Uninitialize the camera now that we're done with it.
        PxLApi.uninitialize(hCamera)
    else:
        print("Could not initialize a camera!")

    return 0


if __name__ == "__main__":
    main()
