"""
getCompressedImage.py

Sample code to enable compression on the camera, grab a couple of images, and
then report on the compression ratio achieved for the images. This sample
uses Pixelink10 compression scheme, and works with either mono or color cameras.
"""

from pixelinkWrapper import*
from ctypes import*
import os

A_OK = 0
GENERAL_ERROR = 1

"""
Checks if a BAYER8 pixel format is being used by the specified camera.
"""
def is_bayer8(pixelFormat):
    if pixelFormat == PxLApi.PixelFormat.BAYER8_RGGB or \
       pixelFormat == PxLApi.PixelFormat.BAYER8_GBRG or \
       pixelFormat == PxLApi.PixelFormat.BAYER8_BGGR or \
       pixelFormat == PxLApi.PixelFormat.BAYER8_GRBG:
        return True

    return False

"""
Returns the frame size of the specified camera using the current camera settings.
"""
def get_frame_size(hCamera, bytesPerPixel):

    # Determine the ROI size
    ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.ROI)
    if not PxLApi.apiSuccess(ret[0]):
        return ret
    params = ret[2]
    width = params[PxLApi.RoiParams.WIDTH]
    height = params[PxLApi.RoiParams.HEIGHT]

    # Determine if there is any pixel addressing applied
    ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.PIXEL_ADDRESSING)
    if not PxLApi.apiSuccess(ret[0]):
        return ret
    params = ret[2]
    paX = params[PxLApi.PixelAddressingParams.X_VALUE]
    paY = params[PxLApi.PixelAddressingParams.Y_VALUE]
    width = width / paX
    height = height / paY

    # Determine if HDR Interleaved is applied
    hdrInterleaveMultiplier = 1

    ret2 = PxLApi.getFeature(hCamera, PxLApi.FeatureId.GAIN_HDR)
    if PxLApi.apiSuccess(ret2[0]):
        params = ret2[2]
        if int(params[0]) == PxLApi.GainHdr.INTERLEAVED:
            hdrInterleaveMultiplier = 2

    width = width * hdrInterleaveMultiplier

    return int(width * height * bytesPerPixel)
    
"""
Save image to a file
This overwrites any existing file
"""
def save_image_to_file(fileName, image, imageSize=0):
    
    assert fileName
    assert len(image) > 0

    # Create a folder to save images if it does not exist 
    if not os.path.exists("getCompressedImage"):
        os.makedirs("getCompressedImage")

    filepath = "getCompressedImage/" + fileName
    # Open a file for binary write
    file = open(filepath, "wb")
    if None == file:
        return GENERAL_ERROR
    numBytesWritten = file.write(image)
    # Resize to a specific image size if requested
    if imageSize > 0:
        file.truncate(imageSize)
    file.close()

    if numBytesWritten == len(image):
        return A_OK

    return GENERAL_ERROR


def main():
    
    file1 = "PxLGetNextFrameImage.bmp"
    file2Bmp = "PxLGetNextCompressedFrameImage.bmp"
    file2Raw = "PxLGetNextCompressedFrame.bin"

    # Step 1
	# Grab a camera
    ret = PxLApi.initialize(0)
    if not PxLApi.apiSuccess(ret[0]):
        print("  Could not find a camera.  rc = {0}".format(ret[0]))
        return GENERAL_ERROR
    hCamera = ret[1]

    # Step 2
    # Make sure the camera is configured correctly:
    #  - Pixel format is either MONO8 or BAYER8
    # And then determine the frame size
    pixelFormat = [PxLApi.PixelFormat.MONO8,]
    ret = PxLApi.getFeature(hCamera, PxLApi.FeatureId.PIXEL_FORMAT)
    if not PxLApi.apiSuccess(ret[0]):
        print("  Unable to get pixel format.  rc = {0}".format(ret[0]))
        PxLApi.uninitialize(hCamera)
        return GENERAL_ERROR
    
    params = ret[2]
    pixelFormat = int(params[0])
    if not pixelFormat == PxLApi.PixelFormat.MONO8 and not is_bayer8(pixelFormat):
        print("  Unknown pixel format.  format = {0}".format(pixelFormat))
        PxLApi.uninitialize(hCamera)
        return GENERAL_ERROR

    frameSize = get_frame_size(hCamera, PxLApi.getBytesPerPixel(pixelFormat))
    if isinstance(frameSize, tuple):
        ret = frameSize
        print("  Unknown frame size.  rc = {0}".format(ret[0]))
        PxLApi.uninitialize(hCamera)
        return GENERAL_ERROR

    # Step 3
    # Enable compression
    params = [pixelFormat, PxLApi.CompressionStrategy.PIXELINK10]
    ret = PxLApi.setFeature(hCamera, PxLApi.FeatureId.COMPRESSION, PxLApi.FeatureFlags.MANUAL, params)
    if not PxLApi.apiSuccess(ret[0]):
        print("  Cannot enable compression.  Are you sure this camera supports it?  rc = {0}".format(ret[0]))
        PxLApi.uninitialize(hCamera)
        return GENERAL_ERROR

    # Step 4
    # Enable the stream
    ret = PxLApi.setStreamState(hCamera, PxLApi.StreamState.START)
    if not PxLApi.apiSuccess(ret[0]):
        print("  Cannot start the stream.  rc = {0}".format(ret[0]))
        PxLApi.uninitialize(hCamera)
        return GENERAL_ERROR

    # Step 5
    # Initialize a few frame buffers, and then capture 2 frames; one compressed and one uncompressed.
    # Frame 1
    frame1Uncompressed = PxLApi.createByteAlignedBuffer(frameSize, 64)
    frame1Desc = None
    # Frame 2
    frame2Compressed = PxLApi.createByteAlignedBuffer(frameSize, 64)
    frame2Uncompressed = PxLApi.createByteAlignedBuffer(frameSize, 64)
    frame2Desc = None
    compressionDesc = create_string_buffer(PxLApi.CompressionDescSize.PIXELINK10)

    ret = PxLApi.getNextFrame(hCamera, frame1Uncompressed)
    if PxLApi.apiSuccess(ret[0]):
        frame1Desc = ret[1]

        ret = PxLApi.getNextCompressedFrame(hCamera, frame2Compressed, compressionDesc)
        print("getNextCompressedFrame returned rc = {0}".format(ret[0]))
    if not PxLApi.apiSuccess(ret[0]):
        print("  Could not capture the frames.  rc = {0}".format(ret[0]))
        ret = PxLApi.setStreamState(hCamera, PxLApi.StreamState.STOP)
        PxLApi.uninitialize(hCamera)
        return GENERAL_ERROR
    frame2Desc = ret[1]

    save_image_to_file(file2Raw, frame2Compressed, int(frame2Desc.CompressionInfo.fCompressedSize))

    # Step 6
    # Decompress frame 2
    ret = PxLApi.decompressFrame(frame2Compressed, frame2Desc, compressionDesc, frame2Uncompressed)
    if not PxLApi.apiSuccess(ret[0]):
        print("  Could not decompress frame 2.  rc = {0}".format(ret[0]))
        ret = PxLApi.setStreamState(hCamera, PxLApi.StreamState.STOP)
        PxLApi.uninitialize(hCamera)
        return GENERAL_ERROR

    # Step 7
    # Create a couple of bitmap images from the 2 captured frames.
    ret = PxLApi.formatImage(frame1Uncompressed, frame1Desc, PxLApi.ImageFormat.BMP)
    if PxLApi.apiSuccess(ret[0]):
        image = ret[1]
        save_image_to_file(file1, image)

    if not PxLApi.apiSuccess(ret[0]):
        print("  Could not save frame 1 as a BMP image.  rc = {0}".format(ret[0]))
        ret = PxLApi.setStreamState(hCamera, PxLApi.StreamState.STOP)
        PxLApi.uninitialize(hCamera)
        return GENERAL_ERROR
        
    ret = PxLApi.formatImage(frame2Uncompressed, frame2Desc, PxLApi.ImageFormat.BMP)
    if PxLApi.apiSuccess(ret[0]):
        image = ret[1]
        save_image_to_file(file2Bmp, image)

    if not PxLApi.apiSuccess(ret[0]):
        print("  Could not save frame 2 as a BMP image.  rc = {0}".format(ret[0]))
        ret = PxLApi.setStreamState(hCamera, PxLApi.StreamState.STOP)
        PxLApi.uninitialize(hCamera)
        return GENERAL_ERROR

    # Step 8
    # Report on the result
    print("  Created {0}; compressed {1:4.2f}:1".format(file1, frameSize / frame1Desc.CompressionInfo.fCompressedSize))
    print("  Created {0}; compressed {1:4.2f}:1".format(file2Bmp, frameSize / frame2Desc.CompressionInfo.fCompressedSize))

    PxLApi.setStreamState(hCamera, PxLApi.StreamState.STOP)
    PxLApi.uninitialize(hCamera)

    return A_OK


if __name__ == "__main__":
    main()
