import time
from queue import Queue
import numpy as np
import pypylon.pylon as py

from CameraManager.CameraManager_MP import CameraManager_MP
import ThermalImageLib as Til

class BaslerCamera(CameraManager_MP):
    def __init__(self, CameraType='Basler', ImageQueue=Queue(maxsize=10)):
        super().__init__(CameraType, ImageQueue)
        self._device_no = None
        self.cam = None
        
        
        self.tlf = py.TlFactory.GetInstance()
        self.no_camera = self.tlf.EnumerateDevices()
        
        
        if not self.no_camera:
            print('No Basler cameras connected')
        else:
            print(f'{self.no_camera} Basler camera detected')
            for i in range(0, self.no_camera):
                self.cam = py.InstantCamera(self.tlf.CreateDevice(self.no_camera[i]))
                self._device_no = i
                self._model = self.GetModelName()
                self._CameraID = self.GetDeviceID()
                self._CameraVersion = self.GetDeviceVersion()
                #self._DriverVersion = self.
                print(f'###{self._device_no}: {CameraType} camera Model : {self._model}// {self._CameraID}// '
                      f'Camera Version: {self._CameraVersion}// Driver Version: {self._DriverVersion}')
        
    @staticmethod
    def Camera_initialize():
        return py.TlFactory.GetInstance()
        
    # @staticmethod
    # def Camera_un_initialize():
    #     return cam = py.InstantCamera(tlf.CreateDevice(devices[0]))

    def Camera_Open(self):
        return self.cam.Open()

    def Camera_Close(self):
        return self.cam.Close()
    
    # Basler Camera Properties
    def getExposureTime(self):
        return self.cam.ExposureTime.GetValue()

    def setExposureTime(self, ExTime):
        self.cam.ExposureTime.SetValue(ExTime)
        
    def getGain(self):
        self.cam.Gain.GetValue()
        
    def setGain(self, gain):
        self.cam.Gain.SetValue(self,gain)
        
    def getWidth(self):
        self.cam.Width.GetValue()
        
    def setWidth(self,width):
        self.cam.Width.SetValue(self,width)
        
    def getHeight(self):
        self.cam.Height.GetValue()
        
    def setHeight(self,height):
        self.cam.Height.SetValue(self,height)
        
    # Basler Camera Capture Functions
    
    def Camera_StartCapture(self):
        return self.cam.StartGrabbing(py.GrabStrategy_LatestImageOnly) 

    def Camera_StopCapture(self):
        return self.cam.StopGrabbing()
    
    
            
    

    def run(self) -> None:
        
        available_cameras = self.cam.EnumerateDevices()
        print("Camera process Starting...")
        self.cam.Open()
        self.cam.StartGrabbing(py.GrabStrategy_OneByOne)
        i = 0
        print('Starting to acquire')
        t0 = time.time()
        while self.cam.IsGrabbing():
            grab = self.cam.RetrieveResult(100, py.TimeoutHandling_ThrowException)
            if grab.GrabSucceeded():
                i += 1
            if i == 100:
                self.cam.StopGrabbing()
                break
        
        print(f'Acquired {i} frames in {time.time()-t0:.0f} seconds')
        camera.Close()
            
    def Camera_LiveCapture(self):
        # Start camera capture
        if self.Camera_StartCapture() is not False:
            window_status = 0
            frame_no = 0
            # Infinite while loop for live capturing
            while window_status >= 0:
                if self.grabResult.GrabSucceeded():
                    # Get data frame from camera
                    data = self.dcam.buf_getlastframedata()
                    window_status, data = self.Camera_ShowFrame(data)

                    # Frame Image processing
                    image = SEip.StrandEnd_Image_Process(self._colormap, data)

                    # Show Processed image at 40% size
                    cv2.imshow('Processed Image', image)
                    cv2.setWindowTitle('Processed Image', f'Processed Thermal Image: {time.strftime("%Y-%m-%d %H:%M:%S")}')
                    cv2.waitKey(1)

                    #Add data to Image Queue
                    if not self._ImageQ.full():
                        self._ImageQ.put(image, block=True, timeout=100)
                        # self._ImagePQ.put()
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
            BasCam.Camera_StopCapture()
        else:
            print(f'Camera Error: Dcam.cap_start() fails with error {self.dcam.lasterr()}')

if __name__ == '__main__':
    ExposureTime = 0.04                                     # Exposure time in sec

    BasCam = BaslerCamera()
    BasCam._colormap = Til.Create_ColorMap(name='afmhot', no_Bits=16, scale=1)
    if BasCam.Camera_Open() is not False:
        #if BasCam.MaxNumBuffer = 5 is not False: #######
        BasCam.ExposureTime.SetValue(ExposureTime)
        print(f'Exposure time set = {BasCam.ExposureTime.SetValue()}')
        BasCam.Camera_LiveCapture()
    else:
        print(f'Camera Error: Dcam.buf_alloc(3) fails with error {BasCam.GrabResult.ErrorDescription}')
        BasCam.Camera_Close()
else:
    print(f'Camera Error: Dcam.dev_open() fails with error {BasCam.GrabResult.ErrorDescription}')
    
    
