import time
from queue import Queue
import numpy as np
import cv2

import dcamapi4 as dc4
from dcam import Dcam, Dcamapi

from CameraManager import CameraManager
import ThermalImageLib as Til
from ImageProcessingLib import StrandEndImageProc as SEip

class HamamatsuCamera(CameraManager):
    def __init__(self, CameraType='Hamamatsu', ImageQueue=Queue(maxsize=10)):
        super().__init__(CameraType, ImageQueue)
        self._device_no = None
        self.dcam = None

        self.Camera_initialize()
        self.no_camera = Dcamapi.get_devicecount()
        if not self.no_camera:
            print(f'No Hamamatsu Cameras connected')
        else:
            print(f'{self.no_camera} Hamamatsu camera detected')
            for i in range(0, self.no_camera):
                self.dcam = Dcam(i)
                self._device_no = i
                self._model = self.dcam.dev_getstring(dc4.DCAM_IDSTR.MODEL)
                self._CameraID = self.dcam.dev_getstring(dc4.DCAM_IDSTR.CAMERAID)
                self._CameraVersion = self.dcam.dev_getstring(dc4.DCAM_IDSTR.CAMERAVERSION)
                self._DriverVersion = self.dcam.dev_getstring(dc4.DCAM_IDSTR.DCAMAPIVERSION)
                print(f'###{self._device_no}: {CameraType} camera Model : {self._model}// {self._CameraID}// '
                      f'Camera Version: {self._CameraVersion}// Driver Version: {self._DriverVersion}')

    @staticmethod
    def Camera_initialize():
        return Dcamapi.init()

    @staticmethod
    def Camera_un_initialize():
        return Dcamapi.uninit()

    def Camera_Open(self):
        return self.dcam.dev_open()

    def Camera_Close(self):
        return self.dcam.dev_close()

    # Hamamatsu Camera Properties
    def getExposureTime(self):
        return self.dcam.prop_getvalue(dc4.DCAM_IDPROP.EXPOSURETIME)

    def setExposureTime(self, ExTime):
        self.dcam.prop_setvalue(dc4.DCAM_IDPROP.EXPOSURETIME, ExTime)

    # Hamamatsu Camera Temperature Sensor
    def getSensorTemp(self):
        return self.dcam.prop_getvalue(dc4.DCAM_IDPROP.SENSORTEMPERATURE)

    def getSensorCoolerMode(self):
        return self.dcam.prop_getvalue(dc4.DCAM_IDPROP.SENSORCOOLER)

    def getSensorCoolerStatus(self):
        return self.dcam.prop_getvalue(dc4.DCAM_IDPROP.SENSORCOOLERSTATUS)

    def getSensorCoolerFan(self):
        return self.dcam.prop_getvalue(dc4.DCAM_IDPROP.SENSORCOOLERFAN)

    def getSensorTempTarget(self):
        return self.dcam.prop_getvalue(dc4.DCAM_IDPROP.SENSORTEMPERATURETARGET)

    def getSensorTemp_Average(self):
        return self.dcam.prop_getvalue(dc4.DCAM_IDPROP.SENSORTEMPERATURE_AVE)

    def getSensorTemp_Min(self):
        return self.dcam.prop_getvalue(dc4.DCAM_IDPROP.SENSORTEMPERATURE_MIN)

    def getSensorTemp_Max(self):
        return self.dcam.prop_getvalue(dc4.DCAM_IDPROP.SENSORTEMPERATURE_MAX)

    def getSensorTemp_Status(self):
        return self.dcam.prop_getvalue(dc4.DCAM_IDPROP.SENSORTEMPERATURE_STATUS)

    def getSensorTemp_Protect(self):
        return self.dcam.prop_getvalue(dc4.DCAM_IDPROP.SENSORTEMPERATURE_PROTECT)

    # Hamamatsu Camera Capture Functions
    def Camera_StartCapture(self):
        return self.dcam.cap_start(True)

    def Camera_StopCapture(self):
        return self.dcam.cap_stop()

    def Camera_CaptureStatus(self):
        return self.dcam.cap_status()

    #
    @staticmethod
    def Camera_ShowFrame(data, window_title='Test', iShown=1):
        """
        Show numpy buffer as an image

        Arg1:   NumPy array
        Arg2:   Window name
        Arg3:   Last window status.
            0   open as a new window
            <0  already closed
            >0  already opened
        """
        # if iShown > 0 and cv2.getWindowProperty(window_title, 0) < 0:
        #     return -1  # Window has been closed
        # if iShown < 0:
        #     return -1  # Window is already closed

        if data.dtype == np.uint16:
            imax = np.amax(data)
            if imax > 0:
                imul = int(65535 / imax)
                # print('Multiple %s' % imul)
                data = data * imul

            # cv2.imshow(window_title, data)
            # cv2.waitKey(1)
            return 1, data
        else:
            print('')
            return -1

    def Generate_Colorbar(self):
        pass

    def Camera_LiveCapture(self):
        # Start camera capture
        if self.Camera_StartCapture() is not False:
            window_status = 0
            frame_no = 0
            # Infinite while loop for live capturing
            while window_status >= 0:
                if self.dcam.wait_capevent_frameready(timeout_millisec=100) is not False:
                    # Get data frame from camera
                    data = self.dcam.buf_getlastframedata()
                    window_status, data = self.Camera_ShowFrame(data)

                    # Frame Image processing
                    image = SEip.Image_Processing(self._colormap, data)

                    # Show Processed image at 40% size
                    cv2.imshow('Processed Image', image)
                    cv2.setWindowTitle('Processed Image', f'Processed Thermal Image: {time.strftime("%Y-%m-%d %H:%M:%S")}')
                    cv2.waitKey(1)

                    #Add data to Image Queue
                    if not self._ImageQ.full():
                        self._ImageQ.put(image, block=True, timeout=100)
                        frame_no += 1
                        if frame_no % 5 == 0:
                            print(f'Frame No.: {frame_no} || Queue Size: {self._ImageQ.qsize()}')
                    else:
                        # self._ImageQ.get()
                        time.sleep(0.2)
                        frame_no += 1
                        print(f'Frame No.: {frame_no} --> Dropped frame no. {frame_no}|| '
                              f'Queue Size: {self._ImageQ.qsize()}')
                else:
                    camera_error = self.dcam.lasterr()
                    if camera_error.is_timeout():
                        print(f'Camera Error: Timeout')
                    else:
                        print(f'Camera Error: wait_event() fails with error {camera_error}')
                        break
            HamCam.Camera_StopCapture()
        else:
            print(f'Camera Error: Dcam.cap_start() fails with error {self.dcam.lasterr()}')


if __name__ == '__main__':
    ExposureTime = 0.04                                     # Exposure time in sec

    HamCam = HamamatsuCamera()
    HamCam._colormap = Til.Create_ColorMap(name='afmhot', no_Bits=16, scale=1)
    if HamCam.Camera_Open() is not False:
        if HamCam.dcam.buf_alloc(3) is not False:
            HamCam.setExposureTime(ExposureTime)
            print(f'Exposure time set = {HamCam.getExposureTime()}')
            HamCam.Camera_LiveCapture()
        else:
            print(f'Camera Error: Dcam.buf_alloc(3) fails with error {HamCam.dcam.lasterr()}')
        HamCam.Camera_Close()
    else:
        print(f'Camera Error: Dcam.dev_open() fails with error {HamCam.dcam.lasterr()}')

    HamCam.Camera_un_initialize()
