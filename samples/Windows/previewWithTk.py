"""
previewWithTk.py

Simple sample application demostrating the use of the API Preview function, 
embedded within a Tkinter window
"""
from pixelinkWrapper import*
from ctypes import*
import ctypes.wintypes
import tkinter as Tk
import threading
import time
import win32api, win32con

"""
Preview control thread -- starts and stops the preview, as well as handles the Windows Dispatch
of the preview window.
"""
def control_preview_thread():
    user32 = windll.user32
    msg = ctypes.wintypes.MSG()
    pMsg = ctypes.byref(msg)
    
    # Create an arror cursor (see below)
    defaultCursor = win32api.LoadCursor(0,win32con.IDC_ARROW)
    
    # Get the current dimensions
    width = topWindow.winfo_width()
    height = topWindow.winfo_height()
    ret = PxLApi.setPreviewSettings(hCamera, "", PxLApi.WindowsPreview.WS_VISIBLE | PxLApi.WindowsPreview.WS_CHILD , 
                                    0, 0, width, height, topHwnd)

    # Start the preview (NOTE: camera must be streaming).  Keep looping until the previewState is STOPed
    ret = PxLApi.setPreviewState(hCamera, PxLApi.PreviewState.START)
    while (PxLApi.PreviewState.START == previewState and PxLApi.apiSuccess(ret[0])):
        if user32.PeekMessageW(pMsg, 0, 0, 0, 1) != 0:
            # All messages are simpy forwarded onto to other Win32 event handlers.  However, we do
            # set the cursor just to ensure that parent windows resize cursors do not persist within
            # the preview window
            win32api.SetCursor(defaultCursor)
            user32.TranslateMessage(pMsg)
            user32.DispatchMessageW(pMsg)
    
    # User has exited -- Stop the preview
    ret = PxLApi.setPreviewState(hCamera, PxLApi.PreviewState.STOP)
    assert PxLApi.apiSuccess(ret[0]), "%i" % ret[0]

"""
Creates a new preview thread for each preview run
"""
def create_new_preview_thread():

    # Creates a thread with preview control / meessage pump
    return threading.Thread(target=control_preview_thread, args=(), daemon=True)

"""
Start the preview (with message pump).
Preview gets stopped when the top level window is closed.
"""
def start_preview():
    # Controls preview thread
    global previewState

    # Declare control preview thread that can control preview and poll the message pump on Windows
    previewState = PxLApi.PreviewState.START
    previewThread = create_new_preview_thread()    
    previewThread.start()

"""
Tkinter Window resize handler
"""
def winResizeHandler(event):
    # The user has resized the window.  Also resize the preview so that the preview will scale to the new window size
    PxLApi.setPreviewSettings(hCamera, "", PxLApi.WindowsPreview.WS_VISIBLE | PxLApi.WindowsPreview.WS_CHILD , 0, 0, event.width, event.height, topHwnd)
    
def main():
    # For simplicity -- share some common (static) variables so they can be used in other threads
    global topWindow
    global menubar

    global hCamera
    global topHwnd
    
    # Step 1
    #      Create our top level window, with a menu bar
    topWindow = Tk.Tk()
    topWindow.title("PixelinkPreview")
    topWindow.geometry("1024x768")

    menubar = Tk.Menu(topWindow)
    filemenu = Tk.Menu(menubar, tearoff=0)
    filemenu.add_command(label="Exit",command=topWindow.quit)
    menubar.add_cascade(label="File", menu=filemenu)
    topWindow.config(menu=menubar)
    
    # Step 2
    #      Set up the camera, including starting the stream
    ret = PxLApi.initialize(0)
    if PxLApi.apiSuccess(ret[0]):
       hCamera = ret[1]

       # Just use all of the camers's current settings.
       # Start the stream
       ret = PxLApi.setStreamState(hCamera, PxLApi.StreamState.START)
       if PxLApi.apiSuccess(ret[0]):

          # Step 3
          #      Start the preview / message pump, as well as the TkInter window resize handler
          topHwnd =  int(topWindow.frame(),0)

          start_preview()
          topWindow.bind('<Configure>', winResizeHandler)
          
          # Step 4
          #      Call the start the UI -- it will only return on Window exit
          topWindow.mainloop()

          # Step 5
          #      The user has quit the appliation, shut down the preview and stream
          previewState = PxLApi.PreviewState.STOP

          # Give preview a bit of time to stop
          time.sleep(0.05)
          
          PxLApi.setStreamState(hCamera, PxLApi.StreamState.STOP) 

       PxLApi.uninitialize(hCamera)


if __name__ == "__main__":
  main()
