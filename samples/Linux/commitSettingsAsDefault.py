"""
commitSettingsAsDefault.py

Little utility program that will commit a cameras settings, to
non volatile memory on the camera. Subsequently, the camera will use these same
settings from a power-up.

This same program can be used to commit the cameras current settings, or the factory
default settings

NOTE: This application assumes there is at most, one Pixelink camera
connected to the system
"""

from pixelinkWrapper import*
import sys
import tty
import termios


def main():
    
    # Step 1 Determine user options.
    if 0 != set_run_options():
        usage()
        return 1
    
    # Step 2 Find and initialize a camera.    
    ret = PxLApi.initialize(0)
    if(not(PxLApi.apiSuccess(ret[0]))):
        print("Could not Initialize the camera! Rc = %i" % ret[0])
        return 1
    hCamera = ret[1]

    if(runOption_useFactoryDefaults):
        print("\nWARNING: This application will commit the cameras factory default settings\n"
              "so that they will be used as the power up defaults.\n"
              "   -- Ok to proceed (y/n)?")
    else:
        print("\nWARNING: This application will commit the cameras current settings\n"
              "so that they will be used as the power up defaults.\n"
              "   -- Ok to proceed (y/n)?")
    
    keyPressed = kbHit()
    
    if 'y' != keyPressed and 'Y' != keyPressed:
        # User aborted.
        PxLApi.uninitialize(hCamera)
        return 0
    
    # Step 3 If requested, load factory defaults.
    if runOption_useFactoryDefaults:
        ret = PxLApi.loadSettings(hCamera, PxLApi.DefaultMemoryChannel.FACTORY_DEFAULTS_MEMORY_CHANNEL)
        assert PxLApi.apiSuccess(ret[0]), "Cannot load factory settings"

    # Step 4 Save the current settings to the user channel.
    ret = PxLApi.saveSettings(hCamera, PxLApi.Settings.SETTINGS_USER)
    print("saveSettings returned %i" % ret[0])

    # Step 5 Done.
    PxLApi.uninitialize(hCamera)
    return 0


def set_run_options():

    global runOption_useFactoryDefaults
    
    useFactoryDefaults = runOption_useFactoryDefaults

    if 1 < len(sys.argv):
        if "-f" == sys.argv[1] or "-F" == sys.argv[1]:
            useFactoryDefaults = True
        else:
            return 1
    
    runOption_useFactoryDefaults = useFactoryDefaults
    return 0

"""
Unbuffered keyboard input on command line.
Keyboard input will be passed to the application without the user pressing
the enter key.
Note: IDLE does not support this functionality.
"""
def kbHit():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

"""
Usage instructions
"""
def usage():
    print("\nSet the power on defaults for the connected camera. Without any parameters,\n"
          "the cameras current parameters will be used. If the '-f' option is specified\n"
          "then the factory default settings will be used.\n")
    print("Usage: %s [options]\n" % sys.argv[0])
    print("   where options are:\n"
          "     -f  Use factory settings as power on defaults")    


if __name__ == "__main__":
    runOption_useFactoryDefaults = False # run options
    main()
