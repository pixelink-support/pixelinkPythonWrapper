# -----------------------------------------------------------------------------
# Copyright (c) 2020 Pixelink a Navitar company
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------

"""
A thin wrapper around the Pixelink 4.0 API that gets distributed
- with Pixelink SDK as the library on Windows
    -- PxLAPI40.dll
or
- with Linux SDK as the library on Linux
    -- libPxLApi.so

Pixelink 4.0 API functions are wrapped using ctypes and exposed as class methods
of the PxLApi class in this module. Consult the Pixelink API documentation for 
specific information - most Pixelink 4.0 API functionality is preserved with a 
few minor limitations, so the regular documentation should suffice for most users. 
Those limitations are documented throughout the wrapper source code.

This wrapper supports all Pixelink cameras that use and are compatible with the 
Pixelink 4.0 API (that is FireWire, USB, USB3, GigE, and 10 GigE cameras). 
The wrapper fully supports functionality of the auto-focus, gain HDR, and polar 
cameras, as well as camera operation with Navitar zoom systems.
"""

from ctypes import*
from ctypes import util
import os
import subprocess

class PxLApi:
    """
    The main class of the wrapper that contains Pixelink API class methods and defines.
    """
    """
    Dynamic link library loader
    The Pixelink 4.0 API library loaded will depend on the operating system
    """
    class _PxlApiRegSettingError(Exception):
        # Pixelink registry key is not present exception
        pass

    if os.name == 'nt': # on Windows
        ## Queries Pixelink registry key
        _regApiCommand = ["REG", "QUERY", "HKEY_CURRENT_USER\\Software\\PixeLINK", "/ve"]
        _pipe = subprocess.Popen(_regApiCommand, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _pipe.communicate()
        _regApiPresent = _pipe.returncode
        if 0 < _regApiPresent:
            raise _PxlApiRegSettingError("The system was unable to find the required Pixelink registry setting")
        
        ## Loads Pixelink API library
        _Api = WinDLL("PxLAPI40.dll")

        ## Verifies that the loaded Pixelink API version is supported
        _minApiVersion = b"4.2.5.11" # minimum Pixelink API version supported
        # Finds Pixelink API full path
        _pxlApiPath = util.find_library("PxLAPI40.dll")
        _pxlApiList = _pxlApiPath.split("\\")
        # Creates Pixelink API full path by making it compatible with wmci
        _wmicApiPath = "name=\'" + "\\\\".join(_pxlApiList) + "\'" 
        _wmicCommand = ["wmic", "datafile", "where", _wmicApiPath, "get", "version"]
        # Queries installed Pixelink API file version 
        _curApiVersion = subprocess.check_output(_wmicCommand).strip(b"Version \r\n")
        # Checks if the loaded Pixelink API is supported
        if _minApiVersion > _curApiVersion:
            print("\nWARNING: Pixelink API Version %s detected. This Python wrapper was designed to\n" 
                  "API Version 4.2.5.11 – upgrade to the latest Pixelink SDK for full functionality and\n"
                  "performance.\n" % str(_curApiVersion, encoding='utf-8'))

    else: # on Linux
        ## Loads Pixelink API library
        _Api = CDLL('libPxLApi.so')

        ## Verifies that the loaded Pixelink API version is supported
        _minApiVersion = b"4.2.2.3" # minimum Pixelink API version supported
        # Searches for installed Pixelink API file and its full path from $PIXELINK_SDK_LIB
        _pxlApiSearch = "find $PIXELINK_SDK_LIB -name 'libPxLApi.so.*'"
        _pxlApiPath = subprocess.check_output(_pxlApiSearch, shell=True).strip()
        # Finds current version of Pixelink API
        _pxlApiList = _pxlApiPath.split(b"/")
        _curApiVersion = _pxlApiList[len(_pxlApiList)-1].strip(b"libPxLApi.so.")
        # Checks if the loaded Pixelink API is supported
        if _minApiVersion > _curApiVersion:
            print("\nWARNING: Pixelink API Version %s detected. This Python wrapper was designed to\n" 
                  "API Version 4.2.2.3 – upgrade to the latest Linux SDK for full functionality and performance.\n"
                  % str(_curApiVersion, encoding='utf-8'))

    """
    Pixelink API class defines
    Equivalent Pixelink 4.0 API defines and their additional information can be 
    found in PixeLINKTypes.h.
    """
    class ClipEncodingFormat:
        PDS = 0
        H264 = 1

    class ClipFileContainerFormat:
        AVI = 0
        MP4 = 1
    
    class FeatureId:
        ALL = -1
        BRIGHTNESS = 0
        PIXELINK_RESERVED_1 = 1
        SHARPNESS = 2
        COLOR_TEMP = 3
        WHITE_BALANCE = 3
        HUE = 4
        SATURATION = 5
        GAMMA = 6
        SHUTTER = 7
        EXPOSURE = 7
        GAIN = 8
        IRIS = 9
        FOCUS = 10
        SENSOR_TEMPERATURE = 11
        TEMPERATURE = 11
        TRIGGER = 12
        ZOOM = 13
        PAN = 14
        TILT = 15
        OPT_FILTER = 16
        GPIO = 17
        FRAME_RATE = 18
        ROI = 19
        FLIP = 20
        PIXEL_ADDRESSING = 21
        DECIMATION = 21
        PIXEL_FORMAT = 22
        EXTENDED_SHUTTER = 23
        AUTO_ROI = 24
        LOOKUP_TABLE = 25
        MEMORY_CHANNEL = 26
        WHITE_SHADING = 27
        ROTATE = 28
        IMAGER_CLK_DIVISOR = 29
        TRIGGER_WITH_CONTROLLED_LIGHT = 30
        MAX_PIXEL_SIZE = 31
        BODY_TEMPERATURE = 32
        MAX_PACKET_SIZE = 33
        BANDWIDTH_LIMIT = 34
        ACTUAL_FRAME_RATE = 35
        SHARPNESS_SCORE = 36
        SPECIAL_CAMERA_MODE = 37	
        GAIN_HDR = 38
        POLAR_WEIGHTINGS = 39
        POLAR_HSV_INTERPRETATION = 40
        PTP = 41
        TOTAL = 42

    class FeatureFlags:
        PRESENCE = 1
        MANUAL = 2
        AUTO = 4
        ONEPUSH = 8
        OFF = 16
        MOD_BITS = 30
        DESC_SUPPORTED = 32
        READ_ONLY = 64
        SETTABLE_WHILE_STREAMING = 128
        PERSISTABLE = 256
        EMULATION = 512
        VOLATILE = 1024
        CONTROLLER = 2048
        ASSERT_LOWER_LIMIT = 4096
        ASSERT_UPPER_LIMIT = 8192
        USES_AUTO_ROI = 16384

    class ImageFormat:
        BMP = 0
        TIFF = 1
        PSD = 2
        JPEG = 3	
        PNG = 4
        RAW_MONO8 = 4096
        RAW_RGB24 = 4101
        RAW_RGB24_DIB = 4101
        RAW_RGB48 = 4102
        RAW_RGB24_NON_DIB = 4114
        RAW_BGR24 = 4130
        RAW_BGR24_NON_DIB = 4130

    class PixelFormat:
        MONO8 = 0
        MONO16 = 1
        YUV422 = 2
        BAYER8_GRBG = 3
        BAYER8 = 3 # generic alias for Bayer8 formats
        BAYER16_GRBG = 4
        BAYER16 = 4 # generic alias for Bayer16 formats
        RGB24 = 5 # generic alias for RGB24_DIB format
        RGB24_DIB = 5
        RGB48 = 6 # generic alias for RGB48_NON_DIB format
        RGB48_NON_DIB = 6
        BAYER8_RGGB = 7
        BAYER8_GBRG = 8
        BAYER8_BGGR = 9
        BAYER16_RGGB = 10
        BAYER16_GBRG = 11
        BAYER16_BGGR = 12	
        MONO12_PACKED = 13
        BAYER12_GRBG_PACKED = 14
        BAYER12_PACKED = 14 # generic alias for Bayer12 formats
        BAYER12_RGGB_PACKED = 15
        BAYER12_GBRG_PACKED = 16
        BAYER12_BGGR_PACKED = 17
        RGB24_NON_DIB = 18
        RGB48_DIB = 19	
        MONO12_PACKED_MSFIRST = 20
        BAYER12_GRBG_PACKED_MSFIRST = 21
        BAYER12_PACKED_MSFIRST = 21 # generic alias for Bayer12 MSFirst formats
        BAYER12_RGGB_PACKED_MSFIRST = 22
        BAYER12_GBRG_PACKED_MSFIRST = 23
        BAYER12_BGGR_PACKED_MSFIRST = 24	
        MONO10_PACKED_MSFIRST = 25
        BAYER10_GRBG_PACKED_MSFIRST = 26
        BAYER10_PACKED_MSFIRST = 26 # generic alias for Bayer10 formats
        BAYER10_RGGB_PACKED_MSFIRST = 27
        BAYER10_GBRG_PACKED_MSFIRST = 28
        BAYER10_BGGR_PACKED_MSFIRST = 29	
        STOKES4_12 = 30
        POLAR4_12 = 31
        POLAR_RAW4_12 = 32
        HSV4_12 = 33	
        BGR24 = 34 # generic alias for BGR24_NON_DIB format
        BGR24_NON_DIB = 34
    
    class StreamState:
        START = 0
        PAUSE = 1
        STOP = 2

    class PreviewState:
        START = 0
        PAUSE = 1
        STOP = 2

    class PreviewWindowEvents:
        CLOSED = 0
        MINIMIZED = 1
        RESTORED = 2
        ACTIVATED = 3
        DEACTIVATED = 4
        RESIZED = 5
        MOVED = 6

    class TriggerTypes:
        FREE_RUNNING = 0
        SOFTWARE = 1
        HARDWARE = 2
        ACTION = 3

    class Descriptors:
        MAX_STROBES = 16
        MAX_KNEE_POINTS = 4

    class DescriptorsAdvancedFeatures:
        UPDATE_CAMERA = 0
        UPDATE_HOST = 1

    class DefaultMemoryChannel:
        FACTORY_DEFAULTS_MEMORY_CHANNEL = 0 # Settings.SETTINGS_FACTORY define can be used instead

    class ControllerFlag:
        FOCUS = 1
        ZOOM = 2
        IRIS = 4
        SHUTTER = 8
        LIGHTING = 16

    class Callback:
        PREVIEW = 1
        # FORMAT_IMAGE = 2 /*(Bugzilla 1776)*/
        FORMAT_CLIP = 4
        FRAME = 8
        PREVIEW_RAW = 16

    class CameraPropertyFlags:
        MONITOR_ACCESS_ONLY = 1
        NOT_ACCESSIBLE = 2
        IP_UNREACHABLE = 4

    class Settings:
        SETTINGS_FACTORY = 0
        SETTINGS_USER = 1

    class ExposureParams:
        VALUE = 0
        AUTO_MIN = 1
        AUTO_MAX = 2

    class Polarity:
        ACTIVE_LOW = 0
        ACTIVE_HIGH = 1
        NEGATIVE = 0
        POSITIVE = 1

    class TriggerParams:
        MODE = 0
        TYPE = 1
        POLARITY = 2
        DELAY = 3
        PARAMETER = 4
        NUMBER = 4
        NUM_PARAMS = 5

    class TriggerModes:
        MODE_0 = 0
        MODE_1 = 1
        MODE_2 = 2
        MODE_3 = 3
        MODE_4 = 4
        MODE_5 = 5
        MODE_14 = 14

    class GpioParams:
        INDEX  = 0
        MODE = 1
        POLARITY = 2
        PARAM_1 = 3
        PARAM_2 = 4
        PARAM_3 = 5
        NUM_PARAMS = 6

    class GpioModes:
        STROBE = 0
        NORMAL = 1
        PULSE = 2
        BUSY = 3
        FLASH = 4
        INPUT = 5
        ACTION_STROBE = 6
        ACTION_NORMAL = 7
        ACTION_PULSE = 8

    class GpioModeStrobe:
        DELAY = 3
        DURATION = 4

    class GpioModePulse:
        NUMBER = 3
        DURATION = 4
        INTERVAL = 5

    class GpioModeInput:
        STATUS = 3

    class RoiParams:
        LEFT = 0
        TOP = 1
        WIDTH = 2
        HEIGHT = 3
        NUM_PARAMS = 4

    class FlipParams:
        HORIZONTAL = 0
        VERTICAL = 1
        NUM_PARAMS = 2

    class SharpnessScoreParams:
        LEFT = 0
        TOP = 1
        WIDTH = 2
        HEIGHT = 3
        MAX_VALUE = 4
        NUM_PARAMS = 5

    class PixelAddressingParams:
        VALUE = 0
        MODE = 1
        X_VALUE = 2
        Y_VALUE = 3
        NUM_PARAMS = 4

    class PixelAddressingModes:
        DECIMATE = 0
        AVERAGE = 1
        BIN = 2
        RESAMPLE = 3

    class PixelAddressingValues:
        VALUE_NONE = 1
        VALUE_BY_2 = 2

    class ExtendedShutterParams:
        NUM_KNEES = 0
        KNEE_1 = 1
        KNEE_2 = 2
        KNEE_3 = 3
        KNEE_4 = 4

    class AutoRoiParams:
        LEFT = 0
        TOP = 1
        WIDTH = 2
        HEIGHT = 3

    class WhiteBalancParams:
        RED = 0
        SHADING_RED = 0
        GREEN = 1
        SHADING_GREEN = 1
        BLUE = 2
        SHADING_BLUE = 2
        NUM_PARAMS = 3

    class Rotate:
        ROTATE_0_DEG = 0
        ROTATE_90_DEG = 90
        ROTATE_180_DEG = 180
        ROTATE_270_DEG = 270

    class MaxPacketSize:
        NORMAL = 1500
        JUMBO = 9000

    class SpecialCameraMode:
        NONE = 0
        FIXED_FRAME_RATE = 1

    class GainHdr:
        NONE = 0
        CAMERA = 1
        INTERLEAVED = 2

    class PolarWeightings:
        WEIGHTINGS_0_DEG = 0
        WEIGHTINGS_45_DEG = 1
        WEIGHTINGS_90_DEG = 2
        WEIGHTINGS_135_DEG = 3

    class PolarHsvInterpretation:
        HSV_AS_COLOR = 0
        HSV_AS_ANGLE = 1
        HSV_AS_DEGREE = 2

    class PtpParams:
        MODE = 0
        STATUS = 1
        ACCURACY = 2
        OFFSET_FROM_MASTER = 3
        NUM_PARAMS = 4

    class PtpModes:
        DISABLED = 0
        AUTOMATIC = 1
        SLAVE_ONLY = 2

    class PtpStatus:
        INITIALIZING = 1
        FAULTY = 2
        DISABLED = 3
        LISTENING = 4
        PREMASTER = 5
        MASTER = 6
        PASSIVE = 7
        UNCALIBRATED = 8
        SLAVE = 9

    class ColorFilterArray:
        CFA_NONE = 0
        CFA_RGGB = 1
        CFA_GBRG = 2
        CFA_GRBG = 3
        CFA_BGGR = 4

    class InitializeExFlags:
        MONITOR_ACCESS_ONLY = 1
        ISSUE_STREAM_STOP = 2

    class IpAddressAssignments:
        UNKNOWN_ASSIGNMENT = 0
        DHCP_ASSIGNED = 1
        LLA_ASSIGNED = 2
        STATIC_PERSISTENT = 3
        STATIC_VOLATILE = 4

    class DataStreamMagicNumber:
        MAGIC_NUMBER = 67372036

    class ClipPlaybackDefaults:
        FRAMERATE_DEFAULT = 30
        FRAMERATE_CAPTURE = -1
        BITRATE_DEFAULT = 1000000
        DECIMATION_NONE = 1

    class EventId:
        ANY = 0
        CAMERA_DISCONNECTED = 1
        HW_TRIGGER_RISING_EDGE = 2
        HW_TRIGGER_FALLING_EDGE = 3
        GPI_RISING_EDGE = 4
        GPI_FALLING_EDGE = 5
        HW_TRIGGER_MISSED = 6
        SYNCHRONIZED_TO_MASTER = 7
        UNSYNCHRONIZED_FROM_MASTER = 8
        FRAMES_SKIPPED = 9
        LAST = 9

    class ActionTypes:
        FRAME_TRIGGER = 0
        GPO1 = 1
        GPO2 = 2
        GPO3 = 3
        GPO4 = 4

    """
    The following preview window defines are used on Windows, but not on Linux
    Their equivalent hexadecimal values are included as comments for convenience.
    """
    class WindowsPreview:
        WS_OVERLAPPED = 0           # 0x00000000
        WS_MAXIMIZEBOX = 65536      # 0x00010000
        WS_MINIMIZEBOX = 131072     # 0x00020000
        WS_THICKFRAME = 262144      # 0x00040000
        WS_SYSMENU = 524288         # 0x00080000
        WS_CAPTION = 12582912       # 0x00C00000
        WS_OVERLAPPEDWINDOW = WS_OVERLAPPED|WS_MAXIMIZEBOX|WS_MINIMIZEBOX|WS_THICKFRAME|WS_SYSMENU|WS_CAPTION
        WS_VISIBLE = 268435456      # 0x10000000
        WS_CHILD = 1073741824       # 0x40000000
    
    """
    ReturnCode class contains Pixelink API error code defines.
    Their equivalent hexadecimal values are included as comments for convenience.
    Equivalent Pixelink 4.0 API defines and their additional information can be found 
    in PixeLINKCodes.h.
    """ 
    class ReturnCode:
        ApiSuccess = 0                                          # 0x0000_0000
        ApiSuccessParametersChanged = 1                         # 0x0000_0001
        ApiSuccessAlreadyRunning = 2                            # 0x0000_0002
        ApiSuccessLowMemory = 3                                 # 0x0000_0003
        ApiSuccessParameterWarning = 4                          # 0x0000_0004
        ApiSuccessReducedSpeedWarning = 5                       # 0x0000_0005
        ApiSuccessExposureAdjustmentMade = 6                    # 0x0000_0006
        ApiSuccessWhiteBalanceTooDark = 7                       # 0x0000_0007
        ApiSuccessWhiteBalanceTooBright = 8                     # 0x0000_0008
        ApiSuccessWithFrameLoss = 9                             # 0x0000_0009
        ApiSuccessGainIneffectiveWarning = 10                   # 0x0000_000A
        ApiSuccessSuspectedFirewallBlockWarning = 11            # 0x0000_000B
        ApiUnknownError = -2147483647                           # 0x8000_0001
        ApiInvalidHandleError = -2147483646                     # 0x8000_0002
        ApiInvalidParameterError = -2147483645                  # 0x8000_0003
        ApiBufferTooSmall = -2147483644                         # 0x8000_0004
        ApiInvalidFunctionCallError = -2147483643               # 0x8000_0005
        ApiNotSupportedError = -2147483642                      # 0x8000_0006
        ApiCameraInUseError = -2147483641                       # 0x8000_0007
        ApiNoCameraError = -2147483640                          # 0x8000_0008
        ApiHardwareError = -2147483639                          # 0x8000_0009
        ApiCameraUnknownError = -2147483638                     # 0x8000_000A
        ApiOutOfBandwidthError = -2147483637                    # 0x8000_000B
        ApiOutOfMemoryError = -2147483636                       # 0x8000_000C
        ApiOSVersionError = -2147483635                         # 0x8000_000D
        ApiNoSerialNumberError = -2147483634                    # 0x8000_000E
        ApiInvalidSerialNumberError = -2147483633               # 0x8000_000F
        ApiDiskFullError = -2147483632                          # 0x8000_0010
        ApiIOError = -2147483631                                # 0x8000_0011
        ApiStreamStopped = -2147483630                          # 0x8000_0012
        ApiNullPointerError = -2147483629                       # 0x8000_0013
        ApiCreatePreviewWndError = -2147483628                  # 0x8000_0014
        ApiOutOfRangeError = -2147483626                        # 0x8000_0016
        ApiNoCameraAvailableError = -2147483625                 # 0x8000_0017
        ApiInvalidCameraName = -2147483624                      # 0x8000_0018
        ApiGetNextFrameBusy = -2147483623                       # 0x8000_0019
        ApiFrameInUseError = -2147483622                        # 0x8000_001A
        ApiStreamExistingError = -1879048191                    # 0x9000_0001
        ApiEnumDoneError = -1879048190                          # 0x9000_0002
        ApiNotEnoughResourcesError = -1879048189                # 0x9000_0003
        ApiBadFrameSizeError = -1879048188                      # 0x9000_0004
        ApiNoStreamError = -1879048187                          # 0x9000_0005
        ApiVersionError = -1879048186                           # 0x9000_0006
        ApiNoDeviceError = -1879048185                          # 0x9000_0007
        ApiCannotMapFrameError = -1879048184                    # 0x9000_0008
        ApiLinkDriverError = -1879048183                        # 0x9000_0009
        ApiInvalidIoctlParameter = -1879048182                  # 0x9000_000A
        ApiInvalidOhciDriverError = -1879048181                 # 0x9000_000B
        ApiCameraTimeoutError = -1879048180                     # 0x9000_000C
        ApiInvalidFrameReceivedError = -1879048179              # 0x9000_000D
        ApiOSServiceError = -1879048178                         # 0x9000_000E
        ApiTimeoutError = -1879048177                           # 0x9000_000F
        ApiRequiresControlAccess = -1879048176                  # 0x9000_0010
        ApiGevInitializationError = -1879048175                 # 0x9000_0011
        ApiIpServicesError = -1879048174                        # 0x9000_0012
        ApiIpAddressingError = -1879048173                      # 0x9000_0013
        ApiDriverCommunicationError = -1879048172               # 0x9000_0014
        ApiInvalidXmlError = -1879048171                        # 0x9000_0015
        ApiCameraRejectedValueError = -1879048170               # 0x9000_0016
        ApiSuspectedFirewallBlockError = -1879048169            # 0x9000_0017
        ApiIncorrectLinkSpeed = -1879048168                     # 0x9000_0018
        ApiCameraNotReady = -1879048167                         # 0x9000_0019
        ApiInconsistentConfiguration = -1879048166              # 0x9000_001A
        ApiNotPermittedWhileStreaming = -1879048165             # 0x9000_001B
        ApiOSAccessDeniedError = -1879048164                    # 0x9000_001C
        ApiInvalidAutoRoiError = -1879048163                    # 0x9000_001D
        ApiGpiHardwareTriggerConflict = -1879048162             # 0x9000_001E
        ApiGpioConfigurationError = -1879048161                 # 0x9000_001F
        ApiUnsupportedPixelFormatError = -1879048160            # 0x9000_0020
        ApiUnsupportedClipEncoding = -1879048159                # 0x9000_0021
        ApiH264EncodingError = -1879048158                      # 0x9000_0022
        ApiH264FrameTooLargeError = -1879048157                 # 0x9000_0023
        ApiH264InsufficientDataError = -1879048156              # 0x9000_0024
        ApiNoControllerError = -1879048155                      # 0x9000_0025
        ApiControllerAlreadyAssignedError = -1879048154         # 0x9000_0026
        ApiControllerInaccessibleError = -1879048153            # 0x9000_0027
        ApiControllerCommunicationError = -1879048152           # 0x9000_0028
        ApiControllerTimeoutError = -1879048151                 # 0x9000_0029
        ApiBufferTooSmallForInterleavedError = -1879048150      # 0x9000_002A
        ApiThisEventNotSupported = -1879048149                  # 0x9000_002B
        ApiFeatureConflictError = -1879048148                   # 0x9000_002C
        ApiGpiOnlyError = -1879048147                           # 0x9000_002D
        ApiGpoOnlyError = -1879048146                           # 0x9000_002E
        ApiInvokedFromIncorrectThreadError = -1879048145        # 0x9000_002F

    """
    The following Pixelink API classes represent wrapped structures.
    Equivalent Pixelink 4.0 API structures and their additional information 
    can be found in PixeLINKTypes.h.
    """
    class _CameraFeatures(Structure):
        
        class _CameraFeature(Structure):
            
            class _FeatureParam(Structure):
                _fields_ = [("fMinValue", c_float),
                            ("fMaxValue", c_float)]
                
            _fields_ = [("uFeatureId", c_uint),
                        ("uFlags", c_uint),
                        ("uNumberOfParameters", c_uint),
                        ("Params", POINTER(_FeatureParam))]
            
        _fields_ = [("uSize", c_uint),
                    ("uNumberOfFeatures", c_uint),
                    ("Features", POINTER(_CameraFeature))]

    class _CameraIdInfo(Structure):
        
        class _MacAddress(Structure):
            _fields_ = [("MacAddr", c_ubyte * 6)]

        class _IpAddress(Structure):

            class _Union(Union):
                _fields_ = [("u8Address", c_ubyte * 4),
                            ("u32Address", c_uint)]

            _fields_ = [("Address", _Union)]

        _fields_ = [("StructSize", c_uint),
                    ("CameraSerialNum", c_uint),
                    ("CameraMac", _MacAddress),
                    ("CameraIpAddress", _IpAddress),
                    ("CameraIpMask", _IpAddress),
                    ("CameraIpGateway", _IpAddress),
                    ("NicIpAddress", _IpAddress),
                    ("NicIpMask", _IpAddress),
                    ("NicAccessMode", c_uint),
                    ("CameraIpAssignmentType", c_ubyte),
                    ("XmlVersionMajor", c_ubyte),
                    ("XmlVersionMinor", c_ubyte),
                    ("XmlVersionSubminor", c_ubyte),
                    ("IpEngineLoadVersionMajor", c_ubyte),
                    ("IpEngineLoadVersionMinor", c_ubyte),
                    ("IpEngineLoadVersionSubminor", c_ubyte),
                    ("CameraProperties", c_ubyte),
                    ("ControllingIpAddress", _IpAddress),
                    ("CameraLinkSpeed", c_uint)]
    
    class _CameraInfo(Structure):
        _fields_ = [("VendorName", c_char * 33),
                    ("ModelName", c_char * 33),
                    ("Description", c_char * 256),
                    ("SerialNumber", c_char * 33),
                    ("FirmwareVersion", c_char * 12),
                    ("FPGAVersion", c_char * 12),
                    ("CameraName", c_char * 256),
                    ("XMLVersion", c_char * 12),
                    ("BootloadVersion", c_char * 12),
                    ("LensDescription", c_char * 64)]

    class ClipEncodingInfo(Structure):
        _fields_ = [("uStreamEncoding", c_uint),
                    ("uDecimationFactor", c_uint),
                    ("playbackFrameRate", c_float),
                    ("playbackBitRate", c_uint)]

    class _ControllerInfo(Structure):
        _fields_ = [("ControllerSerialNumber", c_uint),
                    ("TypeMask", c_uint),
                    ("CameraSerialNumber", c_uint),
                    ("COMPort", c_char * 64),
                    ("USBVitrualPort", c_uint),
                    ("VendorName", c_char * 64),
                    ("ModelName", c_char * 64),
                    ("Description", c_char * 256),
                    ("FirmwareVersion", c_char * 64)]

    class _ErrorReport(Structure):
        _fields_ = [("uReturnCode", c_int),
                    ("strFunctionName", c_char * 32),
                    ("strReturnCode", c_char * 32),
                    ("strReport", c_char * 256)]

    class _FrameDesc(Structure):
    
        class Brightness(Structure):
            _fields_ = [("fValue", c_float)]

        class AutoExposure(Structure):
            _fields_ = [("fValue", c_float)]

        class Sharpness(Structure):
            _fields_ = [("fValue", c_float)]
        
        class WhiteBalance(Structure):
            _fields_ = [("fValue", c_float)]

        class Hue(Structure):
            _fields_ = [("fValue", c_float)]

        class Saturation(Structure):
            _fields_ = [("fValue", c_float)]

        class Gamma(Structure):
            _fields_ = [("fValue", c_float)]

        class Shutter(Structure):
            _fields_ = [("fValue", c_float)]

        class Gain(Structure):
            _fields_ = [("fValue", c_float)]

        class Iris(Structure):
            _fields_ = [("fValue", c_float)]

        class Focus(Structure):
            _fields_ = [("fValue", c_float)]

        class Temperature(Structure):
            _fields_ = [("fValue", c_float)]

        class Trigger(Structure):
            _fields_ = [("fMode", c_float),
                        ("fType", c_float),
                        ("fPolarity", c_float),
                        ("fDelay", c_float),
                        ("fParameter", c_float)]

        class Zoom(Structure):
            _fields_ = [("fValue", c_float)]

        class Pan(Structure):
            _fields_ = [("fValue", c_float)]

        class Tilt(Structure):
            _fields_ = [("fValue", c_float)]

        class OpticalFilter(Structure):
            _fields_ = [("fValue", c_float)]

        class GPIO(Structure):
            _MAX_STROBES = 16
            _fields_ = [("fMode", c_float * _MAX_STROBES),
                        ("fPolarity", c_float * _MAX_STROBES),
                        ("fParameter1", c_float * _MAX_STROBES),
                        ("fParameter2", c_float * _MAX_STROBES),
                        ("fParameter3", c_float * _MAX_STROBES)]

        class FrameRate(Structure):
            _fields_ = [("fValue", c_float)]

        class Roi(Structure):
            _fields_ = [("fLeft", c_float),
                        ("fTop", c_float),
                        ("fWidth", c_float),
                        ("fHeight", c_float)]

        class Flip(Structure):
            _fields_ = [("fHorizontal", c_float),
                    ("fVertical", c_float)]

        class Decimation(Structure):
            _fields_ = [("fValue", c_float)]

        class PixelFormat(Structure):
            _fields_ = [("fValue", c_float)]

        class ExtendedShutter(Structure):
            _MAX_KNEE_POINTS = 4
            _fields_ = [("fKneePoint", c_float * _MAX_KNEE_POINTS)]

        class AutoROI(Structure):
            _fields_ = [("fLeft", c_float),
                        ("fTop", c_float),
                        ("fWidth", c_float),
                        ("fHeight", c_float)]

        class DecimationMode(Structure):
            _fields_ = [("fValue", c_float)]

        class WhiteShading(Structure):
            _fields_ = [("fRedGain", c_float),
                        ("fGreenGain", c_float),
                        ("fBlueGain", c_float)]

        class Rotate(Structure):
            _fields_ = [("fValue", c_float)]

        class ImagerClkDivisor(Structure):
            _fields_ = [("fValue", c_float)]

        class TriggerWithControlledLight(Structure):
            _fields_ = [("fValue", c_float)]

        class MaxPixelSize(Structure):
            _fields_ = [("fValue", c_float)]

        class TriggerNumber(Structure):
            _fields_ = [("fValue", c_float)]

        class ImageProcessing(Structure):
            _fields_ = [("uMask", c_uint)]

        class PixelAddressingValue(Structure):
            _fields_ = [("fHorizontal", c_float),
                        ("fVertical", c_float)]

        class BandwidthLimit(Structure):
            _fields_ = [("fValue", c_float)]

        class ActualFrameRate(Structure):
            _fields_ = [("fValue", c_float)]

        class SharpnessScoreParams(Structure):
            _fields_ = [("fLeft", c_float),
                        ("fTop", c_float),
                        ("fWidth", c_float),
                        ("fHeight", c_float),
                        ("fMaxValue", c_float)]

        class SharpnessScore(Structure):
            _fields_ = [("fValue", c_float)]

        class HDRInfo(Structure):
            _fields_ = [("uMode", c_uint),
                        ("fDarkGain", c_float),
                        ("fBrightGain", c_float)]

        class PolarInfo(Structure):
            _fields_ = [("uCFA", c_uint),
                        ("f0Weight", c_float),
                        ("f45Weight", c_float),
                        ("f90Weight", c_float),
                        ("f135Weight", c_float),
                        ("uHSVInterpretation", c_uint)]

        _fields_ = [("uSize", c_uint),
                    ("fFrameTime", c_float),
                    ("uFrameNumber", c_uint),
                    ("Brightness", Brightness),
                    ("AutoExposure", AutoExposure),
                    ("Sharpness", Sharpness),
                    ("WhiteBalance", WhiteBalance),
                    ("Hue", Hue),
                    ("Saturation", Saturation),
                    ("Gamma", Gamma),
                    ("Shutter", Shutter),
                    ("Gain", Gain),
                    ("Iris", Iris),
                    ("Focus", Focus),
                    ("Temperature", Temperature),
                    ("Trigger", Trigger),
                    ("Zoom", Zoom),
                    ("Pan", Pan),
                    ("Tilt", Tilt),
                    ("OpticalFilter", OpticalFilter),
                    ("GPIO", GPIO),
                    ("FrameRate", FrameRate),
                    ("Roi", Roi),
                    ("Flip", Flip),
                    ("Decimation", Decimation),
                    ("PixelFormat", PixelFormat),
                    ("ExtendedShutter", ExtendedShutter),
                    ("AutoROI", AutoROI),
                    ("DecimationMode", DecimationMode),
                    ("WhiteShading", WhiteShading),
                    ("Rotate", Rotate),
                    ("ImagerClkDivisor", ImagerClkDivisor),
                    ("TriggerWithControlledLight", TriggerWithControlledLight),
                    ("MaxPixelSize", MaxPixelSize),
                    ("TriggerNumber", TriggerNumber),
                    ("ImageProcessing", ImageProcessing),
                    ("PixelAddressingValue", PixelAddressingValue),
                    ("dFrameTime", c_double),
                    ("u64FrameNumber", c_ulonglong),
                    ("BandwidthLimit", BandwidthLimit),
                    ("ActualFrameRate", ActualFrameRate),
                    ("SharpnessScoreParams", SharpnessScoreParams),
                    ("SharpnessScore", SharpnessScore),
                    ("HDRInfo", HDRInfo),
                    ("PolarInfo", PolarInfo)]

    class _IpAddress(Structure):

        class _Union(Union):
            _fields_ = [("u8Address", c_ubyte * 4),
                        ("u32Address", c_uint)]

        _fields_ = [("Address", _Union)]

    class _MacAddress(Structure):
        _fields_ = [("MacAddr", c_ubyte * 6)]
    
    """
    These function prototypes are used as decorator factories for Pixelink 4.0 API functions with 
    callbacks. Their respective Pixelink API functions with callbacks are included in comments. 
    The function prototypes get dynamically selected based on the operating system, and the actual 
    callback functions can be declared using @PxLApi._functionName syntax.
    For example, use of the @PxLApi._dataProcessFunction prototype can be found in the callback.py 
    sample.
    Note: Each of the callback functions are shown to return an error code. This is shown this way 
    to preserve a likeness to the native Pixelink 4.0 API. However, Python users should not rely 
    on this return code. Rather, all error checking should be done within the callback routine 
    itself.
    """
    if os.name == 'nt':
        # used on Windows
        # getClip and getEncodedClip
        _terminationFunction = WINFUNCTYPE(c_uint, c_uint, c_uint, c_int)
        # setCallback
        _dataProcessFunction = WINFUNCTYPE(c_uint, c_uint, POINTER(c_ubyte), c_uint, POINTER(_FrameDesc), c_void_p)
        # setPreviewStateEx
        _changeFunction = WINFUNCTYPE(c_uint, c_uint, c_uint, c_void_p)
        # setEventCallback
        _eventProcessFunction = WINFUNCTYPE(c_uint, c_uint, c_uint, c_double, c_uint, POINTER(c_ubyte), c_void_p)
    else:
        # used on Linux
        # getClip and getEncodedClip
        _terminationFunction = CFUNCTYPE(c_uint, c_uint, c_uint, c_int)
        # setCallback
        _dataProcessFunction = CFUNCTYPE(c_uint, c_uint, POINTER(c_ubyte), c_uint, POINTER(_FrameDesc), c_void_p)
        # setPreviewStateEx
        _changeFunction = CFUNCTYPE(c_uint, c_uint, c_uint, c_void_p)
        # setEventCallback
        _eventProcessFunction = CFUNCTYPE(c_uint, c_uint, c_uint, c_double, c_uint, POINTER(c_ubyte), c_void_p)

    """ 
    Pixelink API functions
    Many of these functions are equivalent to functions found in the native Pixelink 4.0 API.
    More information about these functions can be found in PixeLINKApi.h. If their equivalent 
    Pixelink 4.0 API functions have both base and extended versions, most of them are wrapped 
    with their latter variant.
    Note: The utf-8 encoding is used to avoid platform dependency.
    """

    def apiSuccess(rc):
        return rc >= 0

    def assignController(hCamera, controllerSerialNumber):
        rc = PxLApi._Api.PxLAssignController(hCamera, controllerSerialNumber)
        return (rc,)

    def createDescriptor(hCamera, updateMode):
        ctDescriptorHandle = c_void_p(None)
        rc = PxLApi._Api.PxLCreateDescriptor(hCamera, byref(ctDescriptorHandle), updateMode)
        if(not(PxLApi.apiSuccess(rc))):
            return (rc,)
        return (rc, ctDescriptorHandle.value)

    def formatClip(inputFileName, outputFileName, inputFormat, outputFormat):
        ctaInputFileName = (c_char * len(inputFileName))()
        ctaInputFileName.value = bytes(inputFileName, 'utf-8')
        ctaOutputFileName = (c_char * len(outputFileName))()
        ctaOutputFileName.value = bytes(outputFileName, 'utf-8')
        rc = PxLApi._Api.PxLFormatClipEx(ctaInputFileName.value, ctaOutputFileName.value, inputFormat, outputFormat)
        return (rc,)


    def formatImage(srcImage, srcFrameDesc, outputFormat):
        """
        formatImage expects an image data buffer argument being passed as a mutable ctypes 
        character buffer instance. Such mutable character buffer instance can be created 
        using the ctypes.create_string_buffer() function.
        For example, see getSnapshot.py sample that uses this function.
        """
        ctBufferSize = c_uint(0)
        rc = PxLApi._Api.PxLFormatImage(byref(srcImage), byref(srcFrameDesc), outputFormat, None, byref(ctBufferSize))
        if(not(PxLApi.apiSuccess(rc))):
            return (rc,)
        ctbDstImage = create_string_buffer(ctBufferSize.value)
        rc = PxLApi._Api.PxLFormatImage(byref(srcImage), byref(srcFrameDesc), outputFormat, byref(ctbDstImage), byref(ctBufferSize))
        if(not(PxLApi.apiSuccess(rc))):
            return (rc,)
        return (rc, ctbDstImage)

    def getActions(hCamera):
        ctScheduledTimestamps = c_double(0)
        ctNumberOfTimestamps = c_uint(0)
        rc = PxLApi._Api.PxLGetActions(hCamera, byref(ctScheduledTimestamps), byref(ctNumberOfTimestamps))
        if(not(PxLApi.apiSuccess(rc))):
            return (rc,)
        return (rc, ctScheduledTimestamps.value, ctNumberOfTimestamps.value)

    """
    getBytesPerPixel is often needed as a universal function in calculating the frame size. Hence, 
    it is added for convenience.
    There is no equivalent function in Pixelink 4.0 API.
    """
    def getBytesPerPixel(dataFormat):
        switcher = {
            PxLApi.PixelFormat.MONO8: 1,
            PxLApi.PixelFormat.BAYER8_GRBG: 1,
            PxLApi.PixelFormat.BAYER8_RGGB: 1,
            PxLApi.PixelFormat.BAYER8_GBRG: 1,
            PxLApi.PixelFormat.BAYER8_BGGR: 1,
            PxLApi.PixelFormat.BAYER8: 1,
            PxLApi.PixelFormat.MONO16: 2,
            PxLApi.PixelFormat.YUV422: 2,
            PxLApi.PixelFormat.BAYER16_GRBG: 2,
            PxLApi.PixelFormat.BAYER16_RGGB: 2,
            PxLApi.PixelFormat.BAYER16_GBRG: 2,
            PxLApi.PixelFormat.BAYER16_BGGR: 2,
            PxLApi.PixelFormat.BAYER16: 2,
            PxLApi.PixelFormat.MONO12_PACKED: 1.5,
            PxLApi.PixelFormat.BAYER12_GRBG_PACKED: 1.5,
            PxLApi.PixelFormat.BAYER12_RGGB_PACKED: 1.5,
            PxLApi.PixelFormat.BAYER12_GBRG_PACKED: 1.5,
            PxLApi.PixelFormat.BAYER12_BGGR_PACKED: 1.5,
            PxLApi.PixelFormat.BAYER12_PACKED: 1.5,
            PxLApi.PixelFormat.MONO12_PACKED_MSFIRST: 1.5,
            PxLApi.PixelFormat.BAYER12_GRBG_PACKED_MSFIRST: 1.5,
            PxLApi.PixelFormat.BAYER12_RGGB_PACKED_MSFIRST: 1.5,
            PxLApi.PixelFormat.BAYER12_GBRG_PACKED_MSFIRST: 1.5,
            PxLApi.PixelFormat.BAYER12_BGGR_PACKED_MSFIRST: 1.5,
            PxLApi.PixelFormat.BAYER12_PACKED_MSFIRST: 1.5,
            PxLApi.PixelFormat.MONO10_PACKED_MSFIRST: 1.25,
            PxLApi.PixelFormat.BAYER10_GRBG_PACKED_MSFIRST: 1.25,
            PxLApi.PixelFormat.BAYER10_RGGB_PACKED_MSFIRST: 1.25,
            PxLApi.PixelFormat.BAYER10_GBRG_PACKED_MSFIRST: 1.25,
            PxLApi.PixelFormat.BAYER10_BGGR_PACKED_MSFIRST: 1.25,
            PxLApi.PixelFormat.BAYER10_PACKED_MSFIRST: 1.25,
            PxLApi.PixelFormat.RGB24: 3,
            PxLApi.PixelFormat.RGB24_DIB: 3,
            PxLApi.PixelFormat.RGB24_NON_DIB: 3,
            PxLApi.PixelFormat.BGR24: 3,
            PxLApi.PixelFormat.BGR24_NON_DIB: 3,
            PxLApi.PixelFormat.RGB48: 6,
            PxLApi.PixelFormat.RGB48_NON_DIB: 6,
            PxLApi.PixelFormat.RGB48_DIB: 6,
            PxLApi.PixelFormat.STOKES4_12: 6,
            PxLApi.PixelFormat.POLAR4_12: 6,
            PxLApi.PixelFormat.POLAR_RAW4_12: 6,
            PxLApi.PixelFormat.HSV4_12: 6
            }
        return switcher.get(dataFormat, 0)

    def getCameraFeatures(hCamera, featureId):
        ctBufferSize = c_uint(0)
        rc = PxLApi._Api.PxLGetCameraFeatures(hCamera, featureId, None, byref(ctBufferSize))
        if(not(PxLApi.apiSuccess(rc))):
            return (rc,)
        ctaFeatures = (c_uint * ctBufferSize.value)()
        rc = PxLApi._Api.PxLGetCameraFeatures(hCamera, featureId, byref(ctaFeatures), byref(ctBufferSize))
        if(not(PxLApi.apiSuccess(rc))):
            return (rc,)
        ctCameraFeatures = cast(ctaFeatures, POINTER(PxLApi._CameraFeatures))
        return (rc, ctCameraFeatures.contents)

    def getCameraInfo(hCamera):
        ctCameraInfo = PxLApi._CameraInfo()
        ctInformationSize = sizeof(ctCameraInfo)
        rc = PxLApi._Api.PxLGetCameraInfoEx(hCamera, byref(ctCameraInfo), ctInformationSize)
        if(not(PxLApi.apiSuccess(rc))):
            return (rc,)
        return (rc, ctCameraInfo)

    def getCameraXml(hCamera):
        ctBufferSize = c_uint(0)
        rc = PxLApi._Api.PxLGetCameraXML(hCamera, None, byref(ctBufferSize))
        if(not(PxLApi.apiSuccess(rc))):
            return (rc,)
        ctbXml = create_string_buffer(ctBufferSize.value)
        rc = PxLApi._Api.PxLGetCameraXML(hCamera, byref(ctbXml), byref(ctBufferSize))
        if(not(PxLApi.apiSuccess(rc))):
            return (rc,)
        return (rc, ctbXml)
        
    def getClip(hCamera, numberOfFramesToCapture, fileName, terminationFunction):
        ctafileName = (c_char * len(fileName))()
        ctafileName.value = bytes(fileName, 'utf-8')
        _ctPxLGetClip = PxLApi._Api.PxLGetClip
        _ctPxLGetClip.argtypes = c_uint, c_uint, c_char_p, PxLApi._terminationFunction
        _ctPxLGetClip.restype = c_int
        rc = _ctPxLGetClip(hCamera, numberOfFramesToCapture, ctafileName.value, terminationFunction)
        return (rc,)
    
    def getCurrentTimestamp(hCamera):
        ctCurrentTimestamp = c_double(0)
        rc = PxLApi._Api.PxLGetCurrentTimestamp(hCamera, byref(ctCurrentTimestamp))
        if(not(PxLApi.apiSuccess(rc))):
            return (rc,)
        return (rc, ctCurrentTimestamp.value)
    
    def getEncodedClip(hCamera, numberOfFramesToCapture, fileName, clipInfo, terminationFunction):
        ctafileName = (c_char * len(fileName))()
        ctafileName.value = bytes(fileName, 'utf-8')
        _ctPxLGetEncodedClip = PxLApi._Api.PxLGetEncodedClip
        _ctPxLGetEncodedClip.argtypes = c_uint, c_uint, c_char_p, POINTER(PxLApi.ClipEncodingInfo), PxLApi._terminationFunction
        _ctPxLGetEncodedClip.restype = c_int
        rc = _ctPxLGetEncodedClip(hCamera, numberOfFramesToCapture, ctafileName.value, byref(clipInfo), terminationFunction)
        return (rc,)

    def getErrorReport(hCamera):
        ctErrorReport = PxLApi._ErrorReport()
        rc = PxLApi._Api.PxLGetErrorReport(hCamera, byref(ctErrorReport))
        if(not(PxLApi.apiSuccess(rc))):
            return (rc,)
        return (rc, ctErrorReport)

    def getFeature(hCamera, featureId, params=None):
        """
        Like all pixelinkWrapper functions, getFeature returns a tuple with number of elements. 
        More specifically, getFeature returns:
            ret[0] - Return code
            ret[1] - A bit mask of PxLApi.FeatureFlags
            ret[2] - A list of paramters. The number of elements in the list varies with the feature
        For example, see getFeature.py sample that uses this function.
        """
        ctFlags = c_uint(0)
        ctNumParams = c_uint(0)
        rc = PxLApi._Api.PxLGetFeature(hCamera, featureId, byref(ctFlags), byref(ctNumParams), None)
        if(not(PxLApi.apiSuccess(rc))):
            return (rc,)
        ctNumParams = c_uint(ctNumParams.value)
        ctaParams = (c_float * ctNumParams.value)()
        if(None != params):
            ctaParams[0] = params[0]
        rc = PxLApi._Api.PxLGetFeature(hCamera, featureId, byref(ctFlags), byref(ctNumParams), byref(ctaParams))
        if(not(PxLApi.apiSuccess(rc))):
            return (rc,)
        params = []
        for i in range(len(ctaParams)):
            params.append(ctaParams[i])
        return (rc, ctFlags.value, params)


    def getNextFrame(hCamera, frame):
        """
        getNextFrame expects a frame data buffer argument being passed as a mutable ctypes character buffer
        instance. Such mutable ctypes character buffer can be created using the ctypes.create_string_buffer() 
        function. When this function gets returned with the success code, this buffer holds frame data that 
        can be further passed to the formatImage function.
        For example, see getSnapshot.py sample that uses both functions.
        """
        if (None == frame or 0 == frame):
            ctBufferSize = -1
            ctFrameDesc = PxLApi._FrameDesc()
            ctFrameDesc.uSize = sizeof(ctFrameDesc)
            rc = PxLApi._Api.PxLGetNextFrame(hCamera, ctBufferSize, frame, byref(ctFrameDesc))
            if(not(PxLApi.apiSuccess(rc))):
                return (rc,)
            return (rc, ctFrameDesc)
        else:
            ctFrameDesc = PxLApi._FrameDesc()
            ctFrameDesc.uSize = sizeof(ctFrameDesc)
            ctBufferSize = len(frame)
            rc = PxLApi._Api.PxLGetNextFrame(hCamera, ctBufferSize, byref(frame), byref(ctFrameDesc))
            if(not(PxLApi.apiSuccess(rc))):
                return (rc,)
        return (rc, ctFrameDesc)
    
    def getNumberCameras():
        """
        Like all pixelinkWrapper functions, getNumberCameras returns a tuple with a number of elements. 
        More specifically, getNumberCameras returns: 
            ret[0] - Return code
            ret[1] - A list of PxLApi._CameraIdInfo(s), with an element for each camera found
        For example, see getNumberCameras.py sample that uses this function.
        """
        ctNumberCameraIds = c_uint(0)
        rc = PxLApi._Api.PxLGetNumberCamerasEx(None, byref(ctNumberCameraIds))
        if(not(PxLApi.apiSuccess(rc))):
            return (rc,)
        ctaCameraIdInfo = (PxLApi._CameraIdInfo * ctNumberCameraIds.value)()
        ctaCameraIdInfo[0].StructSize = sizeof(PxLApi._CameraIdInfo)
        rc = PxLApi._Api.PxLGetNumberCamerasEx(byref(ctaCameraIdInfo), byref(ctNumberCameraIds))
        if(not(PxLApi.apiSuccess(rc))):
            return (rc,)
        cameraIdInfo = []
        for i in range(len(ctaCameraIdInfo)):
            cameraIdInfo.append(ctaCameraIdInfo[i])
        return (rc, cameraIdInfo)

    def getNumberControllers():
        ctControllerInfo = PxLApi._ControllerInfo()
        ctInformationSize = sizeof(ctControllerInfo)
        ctNumberControllerInfos = c_uint(0)            
        rc = PxLApi._Api.PxLGetNumberControllers(None, ctInformationSize, byref(ctNumberControllerInfos))
        if(not(PxLApi.apiSuccess(rc))):
            return (rc,)
        ctaControllerInfo = (PxLApi._ControllerInfo * ctNumberControllerInfos.value)()
        rc = PxLApi._Api.PxLGetNumberControllers(byref(ctaControllerInfo), ctInformationSize, byref(ctNumberControllerInfos))
        if(not(PxLApi.apiSuccess(rc))):
            return (rc,)
        controllerInfo = []
        for i in range(len(ctaControllerInfo)):
            controllerInfo.append(ctaControllerInfo[i])
        return (rc, controllerInfo)

    """
    imageSize is often needed to determine the frame size. Hence, it is added for convenience.
    There is no equivalent function in Pixelink 4.0 API.
    """
    def imageSize(frameDesc):
        return int((frameDesc.Roi.fWidth/frameDesc.PixelAddressingValue.fHorizontal)*
                   (frameDesc.Roi.fHeight/frameDesc.PixelAddressingValue.fVertical)*
                    PxLApi.getBytesPerPixel(frameDesc.PixelFormat.fValue))
        
    def initialize(serialNumber, flags=0):
        cthCamera = c_void_p(None)
        rc = PxLApi._Api.PxLInitializeEx(serialNumber, byref(cthCamera), flags)
        if(not(PxLApi.apiSuccess(rc))):
            return (rc,)
        return (rc, cthCamera.value)

    def loadSettings(hCamera, channel):
        rc = PxLApi._Api.PxLLoadSettings(hCamera, channel)
        return (rc,)

    def removeDescriptor(hCamera, hDescriptor):
        rc = PxLApi._Api.PxLRemoveDescriptor(hCamera, hDescriptor)
        return (rc,)

    def resetPreviewWindow(hCamera):
        rc = PxLApi._Api.PxLResetPreviewWindow(hCamera)
        return (rc,)

    def saveSettings(hCamera, channel):
        rc = PxLApi._Api.PxLSaveSettings(hCamera, channel)
        return (rc,)

    def setActions(actionType, scheduledTimestamp):
        ctScheduledTimestamps = c_double(scheduledTimestamp)
        rc = PxLApi._Api.PxLSetActions(actionType, ctScheduledTimestamps)
        return (rc,)
    
    def setCallback(hCamera, callbackType, context, dataProcessFunction):        
        _ctPxLSetCallback = PxLApi._Api.PxLSetCallback
        if 0 == dataProcessFunction or None == dataProcessFunction:
            _ctPxLSetCallback.argtypes = c_uint, c_uint, c_void_p, c_uint
            _ctPxLSetCallback.restype = c_int
            rc = _ctPxLSetCallback(hCamera, callbackType, context, 0)
        else:
            _ctPxLSetCallback.argtypes = c_uint, c_uint, c_void_p, PxLApi._dataProcessFunction
            _ctPxLSetCallback.restype = c_int
            rc = _ctPxLSetCallback(hCamera, callbackType, context, dataProcessFunction)
        return (rc,)
    
    def setCameraIpAddress(cameraMac, cameraIp, cameraSubnetMask, cameraDefaultGateway, persistent):
        ctCameraMac = PxLApi._MacAddress()
        ctCameraIp = PxLApi._IpAddress()
        ctCameraSubnetMask = PxLApi._IpAddress()
        ctCameraDefaultGateway = PxLApi._IpAddress()
        for i in range(len(cameraMac)):
            if i > (len(ctCameraMac.MacAddr)-1):
                break
            ctCameraMac.MacAddr[i] = cameraMac[i]
        for i in range(len(cameraIp)):
            if i > (len(ctCameraIp.Address.u8Address)-1):
                break
            ctCameraIp.Address.u8Address[i] = cameraIp[i]
        for i in range(len(cameraSubnetMask)):
            if i > (len(ctCameraSubnetMask.Address.u8Address)-1):
                break
            ctCameraSubnetMask.Address.u8Address[i] = cameraSubnetMask[i]
        for i in range(len(cameraDefaultGateway)):
            if i > (len(ctCameraDefaultGateway.Address.u8Address)-1):
                break
            ctCameraDefaultGateway.Address.u8Address[i] = cameraDefaultGateway[i]
        rc = PxLApi._Api.PxLSetCameraIpAddress(byref(ctCameraMac), byref(ctCameraIp), byref(ctCameraSubnetMask), byref(ctCameraDefaultGateway), persistent)
        return (rc,)

    def setCameraName(hCamera, cameraName):
        ctaCameraName = (c_char * len(cameraName))()
        ctaCameraName.value = bytes(cameraName, 'utf-8')
        rc = PxLApi._Api.PxLSetCameraName(hCamera, ctaCameraName.value)
        return (rc,)

    def setEventCallback(hCamera, eventId, context, eventProcessFunction):
        _ctPxLSetEventCallback = PxLApi._Api.PxLSetEventCallback
        if 0 == eventProcessFunction or None == eventProcessFunction:
            _ctPxLSetEventCallback.argtypes = c_uint, c_uint, c_void_p, c_uint
            _ctPxLSetEventCallback.restype = c_int
            rc = _ctPxLSetEventCallback(hCamera, eventId, context, 0)
        else:
            _ctPxLSetEventCallback.argtypes = c_uint, c_uint, c_void_p, PxLApi._eventProcessFunction
            _ctPxLSetEventCallback.restype = c_int
            rc = _ctPxLSetEventCallback(hCamera, eventId, context, eventProcessFunction)
        return (rc,)

    def setFeature(hCamera, featureId, flags, params):
        ctNumParams = len(params)
        ctaParams = (c_float * ctNumParams)()
        for i in range(len(ctaParams)):
            if i > (len(params)-1):
                break
            ctaParams[i] = params[i]
        rc = PxLApi._Api.PxLSetFeature(hCamera, featureId, flags, ctNumParams, byref(ctaParams))
        return (rc,)

    def setPreviewSettings(hCamera, title="Pixelink Preview", style=WindowsPreview.WS_OVERLAPPEDWINDOW|WindowsPreview.WS_VISIBLE, 
                           left=0, top=0, width=640, height=480, parent=0):
        ctaTitle = (c_char * len(title))()
        ctaTitle.value = bytes(title, 'utf-8')
        ctChildId = 0 # this parameter is not used in the Python wrapper
        if os.name == 'nt':
            cthParent = c_void_p(parent) # Windows can accomodate preview as a child window
        else:
            cthParent = c_void_p(None) # Child windows not defined on Linux
            style = 0 # is used on Linux
        rc = PxLApi._Api.PxLSetPreviewSettings(hCamera, ctaTitle.value, style, left, top, width, height, cthParent, ctChildId)
        return (rc,)

    def setPreviewState(hCamera, previewState):
        cthWnd = c_void_p(None)
        rc = PxLApi._Api.PxLSetPreviewState(hCamera, previewState, byref(cthWnd))
        if(not(PxLApi.apiSuccess(rc))):
            return (rc,)
        return (rc, cthWnd.value)

    def setPreviewStateEx(hCamera, previewState, context, changeFunction):
        cthWnd = c_void_p(None)
        _ctPxLSetPreviewStateEx = PxLApi._Api.PxLSetPreviewStateEx
        _ctPxLSetPreviewStateEx.argtypes = c_uint, c_uint, c_void_p, c_void_p, PxLApi._changeFunction
        _ctPxLSetPreviewStateEx.restype = c_int
        rc = _ctPxLSetPreviewStateEx(hCamera, previewState, byref(cthWnd), context, changeFunction)
        if(not(PxLApi.apiSuccess(rc))):
            return (rc,)
        return (rc, cthWnd.value)
        
    def setStreamState(hCamera, streamState):
        rc = PxLApi._Api.PxLSetStreamState(hCamera, streamState)
        return (rc,)

    def unassignController(hCamera, controllerSerialNumber):
        rc = PxLApi._Api.PxLUnassignController(hCamera, controllerSerialNumber)
        return (rc,)

    def uninitialize(hCamera):
        rc = PxLApi._Api.PxLUninitialize(hCamera)
        return (rc,)

    def updateDescriptor(hCamera, hDescriptor, updateMode):
        rc = PxLApi._Api.PxLUpdateDescriptor(hCamera, hDescriptor, updateMode)
        return (rc,)
