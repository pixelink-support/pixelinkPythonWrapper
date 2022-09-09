"""
previewWithPyQt5.py

Simple sample application demonstrating the use of the API Preview function, 
embedded within a PyQt5 windows

PyQt5 needs to be installed to run this sample (e.g.: 'pip install PyQt5')
to locate the appropriate libaries.
"""
from pixelinkWrapper import*
from ctypes import*
import ctypes.wintypes
import threading
import time
import sys

from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QAction
from PyQt5.QtCore import QThread

"""
PyQt5 top-level window with a menu bar and a preview window
"""
class MainWindow(QMainWindow):
    # Create our top-level window with a menu bar and a preview window
    def __init__(self, parent=None):
        # Initializer
        super().__init__(parent)
        # Main Window's properties
        self.setWindowTitle("PixelinkPreview")
        self.setGeometry(0, 0, 1024, 768)
        # Create and set the central widget as
        self.previewWindow = PreviewWindow(self)
        self.setCentralWidget(self.previewWindow)   
        # Set the menu bar with actions
        self._createActions()
        self._createMenuBar()
        # Start using the camera
        self._startCamera()

    def _createActions(self):
        self.exitAction = QAction("&Exit", self)
        self.exitAction.triggered.connect(self.exitApp)

    def _createMenuBar(self):
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu("&File")
        fileMenu.addAction(self.exitAction)

    def _startCamera(self):
        # Set up the camera and start the stream
        ret = PxLApi.initialize(0)
        if PxLApi.apiSuccess(ret[0]):
            self.hCamera = ret[1]
            # Just use all of the camera's current settings.
            # Start the stream and preview
            ret = PxLApi.setStreamState(self.hCamera, PxLApi.StreamState.START)
            if PxLApi.apiSuccess(ret[0]):
                self._startPreview()

    # Start preview (with message pump). Preview gets stopped when the top level window is closed.
    def _startPreview(self):
        self.previewWindow.previewState = PxLApi.PreviewState.START
        self.previewWindow.previewThread.start()

    def _stopCamera(self):
        # The user has quit the appliation, shut down the preview and stream
        self.previewWindow.previewState = PxLApi.PreviewState.STOP
        # Give preview a bit of time to stop
        time.sleep(0.05)
          
        PxLApi.setStreamState(self.hCamera, PxLApi.StreamState.STOP)

        PxLApi.uninitialize(self.hCamera)

    def exitApp(self):
        self.close()

    def closeEvent(self, event):
        # The user has quit the application, stop using the camera
        self._stopCamera()
        return super().closeEvent(event)
        
"""
PyQt5 Preview window with the API preview control
"""
class PreviewWindow(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.mainWindow = parent
        self.winId = int(self.winId())
        self.previewState = PxLApi.PreviewState.STOP    # default preview state
        self.previewThread = ControlPreview(self)
        
    # Window resize handler
    def resizeEvent(self, event):        
        # The user has resized the window. Also resize the preview so that the preview will scale to the new window size
        hCamera = self.mainWindow.hCamera
        width = event.size().width()
        height = event.size().height()
        previewHwnd = self.winId
        PxLApi.setPreviewSettings(hCamera, "", PxLApi.WindowsPreview.WS_VISIBLE | PxLApi.WindowsPreview.WS_CHILD , 0, 0, width, height, previewHwnd)


"""
Preview control QThread -- starts and stops the preview, as well as handles the Windows Dispatch
of the preview window.
"""
class ControlPreview(QThread):

    def __init__(self, parent=None):
        super().__init__()
        self.previewWindow = parent
       
    def run(self):
        # Run preview function
        self._runPreview()

    def _runPreview(self):
        user32 = windll.user32
        msg = ctypes.wintypes.MSG()
        pMsg = ctypes.byref(msg)
        
        # Get the current dimensions of the Preview Window
        hCamera = self.previewWindow.mainWindow.hCamera
        width = self.previewWindow.size().width()
        height = self.previewWindow.size().height()
        previewHwnd = self.previewWindow.winId

        # Start the stream in case the camera is not streaming
        ret = PxLApi.setStreamState(hCamera, PxLApi.StreamState.START)
        assert PxLApi.apiSuccess(ret[0]), "%i" % ret[0]

        # Set preview settings
        ret = PxLApi.setPreviewSettings(hCamera, "", PxLApi.WindowsPreview.WS_VISIBLE | PxLApi.WindowsPreview.WS_CHILD, 
                                        0, 0, width, height, previewHwnd)

        # Start the preview (NOTE: camera must be streaming). Keep looping until the previewState is STOPed
        ret = PxLApi.setPreviewState(hCamera, PxLApi.PreviewState.START)
        while (PxLApi.PreviewState.START == self.previewWindow.previewState and PxLApi.apiSuccess(ret[0])):
            if user32.PeekMessageW(pMsg, 0, 0, 0, 1) != 0:
                # All messages are simlpy forwarded onto to other Win32 event handlers. However, we do
                # set the cursor just to ensure that parent windows resize cursors do not persist within
                # the preview window
                user32.TranslateMessage(pMsg)
                user32.DispatchMessageW(pMsg)
    
        # User has exited -- Stop the preview
        ret = PxLApi.setPreviewState(hCamera, PxLApi.PreviewState.STOP)
        assert PxLApi.apiSuccess(ret[0]), "%i" % ret[0]


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())
