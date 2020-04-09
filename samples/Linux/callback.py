"""
callback.py

Demonstrates how to use callbacks with Callback.PREVIEW
The callback function here does not modify the image data.
"""

from pixelinkWrapper import*
import time
import threading


def get_pixel_format_as_string(dataFormat):
    switcher = {
        PxLApi.PixelFormat.MONO8: "MONO8",
        PxLApi.PixelFormat.MONO16: "MONO16",
        PxLApi.PixelFormat.YUV422: "YUV422",
        PxLApi.PixelFormat.BAYER8_GRBG: "BAYER8_GRBG",
        PxLApi.PixelFormat.BAYER16_GRBG: "BAYER16_GRBG",
        PxLApi.PixelFormat.RGB24: "RGB24",
        PxLApi.PixelFormat.RGB48: "RGB48",
        PxLApi.PixelFormat.BAYER8_RGGB: "BAYER8_RGGB",
        PxLApi.PixelFormat.BAYER8_GBRG: "BAYER8_GBRG",
        PxLApi.PixelFormat.BAYER8_BGGR: "BAYER8_BGGR",
        PxLApi.PixelFormat.BAYER16_RGGB: "BAYER16_RGGB",
        PxLApi.PixelFormat.BAYER16_GBRG: "BAYER16_GBRG",
        PxLApi.PixelFormat.BAYER16_BGGR: "BAYER16_BGGR",
        PxLApi.PixelFormat.MONO12_PACKED: "MONO12_PACKED",
        PxLApi.PixelFormat.BAYER12_GRBG_PACKED: "BAYER12_GRBG_PACKED",
        PxLApi.PixelFormat.BAYER12_RGGB_PACKED: "BAYER12_RGGB_PACKED",
        PxLApi.PixelFormat.BAYER12_GBRG_PACKED: "BAYER12_GBRG_PACKED",
        PxLApi.PixelFormat.BAYER12_BGGR_PACKED: "BAYER12_BGGR_PACKED",
        PxLApi.PixelFormat.RGB24_NON_DIB: "RGB24_NON_DIB",
        PxLApi.PixelFormat.RGB48_DIB: "RGB48_DIB",
        PxLApi.PixelFormat.MONO12_PACKED_MSFIRST: "MONO12_PACKED_MSFIRST",
        PxLApi.PixelFormat.BAYER12_GRBG_PACKED_MSFIRST: "BAYER12_GRBG_PACKED_MSFIRST",
        PxLApi.PixelFormat.BAYER12_RGGB_PACKED_MSFIRST: "BAYER12_RGGB_PACKED_MSFIRST",
        PxLApi.PixelFormat.BAYER12_GBRG_PACKED_MSFIRST: "BAYER12_GBRG_PACKED_MSFIRST",
        PxLApi.PixelFormat.BAYER12_BGGR_PACKED_MSFIRST: "BAYER12_BGGR_PACKED_MSFIRST",
        PxLApi.PixelFormat.MONO10_PACKED_MSFIRST: "MONO10_PACKED_MSFIRST",
        PxLApi.PixelFormat.BAYER10_GRBG_PACKED_MSFIRST: "BAYER10_GRBG_PACKED_MSFIRST",
        PxLApi.PixelFormat.BAYER10_RGGB_PACKED_MSFIRST: "BAYER10_RGGB_PACKED_MSFIRST",
        PxLApi.PixelFormat.BAYER10_GBRG_PACKED_MSFIRST: "BAYER10_GBRG_PACKED_MSFIRST",
        PxLApi.PixelFormat.BAYER10_BGGR_PACKED_MSFIRST: "BAYER10_BGGR_PACKED_MSFIRST",
        PxLApi.PixelFormat.STOKES4_12: "STOKES4_12",
        PxLApi.PixelFormat.POLAR4_12: "POLAR4_12",
        PxLApi.PixelFormat.POLAR_RAW4_12: "POLAR_RAW4_12",
        PxLApi.PixelFormat.HSV4_12: "HSV4_12",
        PxLApi.PixelFormat.BGR24_NON_DIB: "BGR24_NON_DIB"        
        }
    return switcher.get(dataFormat, "Unknown data format")

"""
Callback function called by the API just before an image is displayed in the preview window. 
N.B. This is called by the API on a thread created in the API.
"""
@PxLApi._dataProcessFunction
def callback_format_preview(hCamera, frameData, dataFormat, frameDesc, userData):
    # Copy frame descriptor information
    frameDescriptor = frameDesc.contents
    # Find image size
    imageSize = int(frameDescriptor.Roi.fWidth * frameDescriptor.Roi.fHeight *
                    PxLApi.getBytesPerPixel(dataFormat))


    print("callback_format_image: hCamera = {0}, frameData = {1}".format(hex(hCamera),
                                                                         hex(id(frameData))))
    print("    dataFormat = {0} {1}, FrameDesc = {2}".format(dataFormat,
                                                             get_pixel_format_as_string(dataFormat),
                                                             hex(id(frameDesc))))
    print("    userData = {0}, threadId = {1}".format(hex(userData), hex(id(threading.current_thread()))))
    print("    imageData = {0} {1} {2} {3} {4} {5} {6} {7}\n".format(hex(frameData[0]), hex(frameData[1]), hex(frameData[2]),
                                                                   hex(frameData[3]), hex(frameData[4]), hex(frameData[5]),
                                                                   hex(frameData[6]), hex(frameData[7])))
    
    # Just to see the effect of the callback, increase intensity of the middle to 100%
    startRow = int((frameDescriptor.Roi.fHeight/5)*2)
    endRow = int((frameDescriptor.Roi.fHeight/5)*3)
    startCol = int((frameDescriptor.Roi.fWidth/5)*2)
    endCol = int((frameDescriptor.Roi.fWidth/5)*3)

    # Find the first pixel that needs to be modified
    bytesPerPixel = PxLApi.getBytesPerPixel(dataFormat)
    
    for i in range(startRow, endRow):
        pixel = int(bytesPerPixel * ((startRow * frameDescriptor.Roi.fWidth) + startCol))
        for j in range(startCol, endCol):
            for k in range(bytesPerPixel):
                index = pixel + k
                frameData[index] = 0xff
            pixel += bytesPerPixel
        startRow += 1

    return 0


def do_callback_on_preview(hCamera):
    # Set the callback function
    print("=====================================================\n")
    print("do_callback_on_preview\n")
    userData = 3735928559
    print("Registering PREVIEW callback with userData {0}\n".format(hex(userData)))
    ret = PxLApi.setCallback(hCamera, PxLApi.Callback.PREVIEW, userData, callback_format_preview)
    if(not(PxLApi.apiSuccess(ret[0]))):
        print("ERROR setting callback function: {0}".format(ret[0]))
        return
    
    ret = PxLApi.setStreamState(hCamera, PxLApi.StreamState.START)
    if(not(PxLApi.apiSuccess(ret[0]))):
        print("ERROR setting stream state function: {0}".format(ret[0]))
        return

    # We will start getting our callback called after we start previewing
    ret = PxLApi.setPreviewState(hCamera, PxLApi.PreviewState.START)
    if(not(PxLApi.apiSuccess(ret[0]))):
        print("ERROR setting preview state function: {0}".format(ret[0]))
        return

    time.sleep(10) # Sleep 10 seconds

    # Stop previewing
    ret = PxLApi.setPreviewState(hCamera, PxLApi.PreviewState.STOP)
    if(not(PxLApi.apiSuccess(ret[0]))):
        print("ERROR setting preview state function: {0}".format(ret[0]))
        return

    ret = PxLApi.setStreamState(hCamera, PxLApi.StreamState.STOP)

    # Disable callback on preview by setting the callback function to 0 or None
    ret = PxLApi.setCallback(hCamera, PxLApi.Callback.PREVIEW, userData, 0)


def main():
    
    ret = PxLApi.initialize(0)
    if(not(PxLApi.apiSuccess(ret[0]))):
        print("ERROR: {0}\n".format(ret[0]))
        return 1
    hCamera = ret[1]
    print("\nMain thread id = {}\n".format(hex(id(threading.current_thread()))))
    
    # do_callback_on_format_image(hCamera) /* Callback.FORMAT_IMAGE is not supported */
    do_callback_on_preview(hCamera)

    PxLApi.uninitialize(hCamera)
    return 0

if __name__ == "__main__":
    main()
