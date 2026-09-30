"""
############
DESCRIPTION:
############

#####
TO DO:
#####
1- Add Message Queue to change properties while camera process is running
2- Test changing colormap while process is running
3- Test changing exposure time and restarting the camera live capture
4- Test changing image rendering size while process is running
4- Overlay frame timestamp and max temperature on every image
5- Add logging functionality and remove print statements
#####
BUGS:
#####
-> dcam_detect_devices_no() method causes crash of Python interpreter with error
    {Process finished with exit code -1073741819 (0xC0000005)} _ The bug crashes the debugger as well, and the line at
    which it occurs can sometime change. The assumption right now is that it can be an issue with the underlying API
"""
import gc
import os
import sys
import importlib
import logging
import time
import datetime

import numpy as np
import cv2

# import dcamapi4 as dc4
# import dcam

try:
    import dcamapi4 as dc4
    import dcam
except ImportError:
    # absolute_path_to_file_directory = os.path.abspath(os.path.join(path, os.pardir))
    MODULE_PATH = "./Hamamatsu/__init__.py"
    # print(MODULE_PATH)
    MODULE_NAME = "Hamamatsu"
    spec = importlib.util.spec_from_file_location(MODULE_NAME, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    import Hamamatsu.dcamapi4 as dc4
    import Hamamatsu.dcam as dcam

# get current directory
# path = os.getcwd()

try:
    import ThermalImageLib as Til
except ImportError:
    # absolute_path_to_file_directory = os.path.abspath(os.path.join(path, os.pardir))
    MODULE_PATH = "ThermalImageLib/__init__.py"
    # print(MODULE_PATH)
    MODULE_NAME = "ThermalImageLib"
    spec = importlib.util.spec_from_file_location(MODULE_NAME, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    import ThermalImageLib as Til

try:
    from CameraManager.CameraManager_MP import CameraManager_MP
except ImportError:
    MODULE_PATH = "CameraManager/__init__.py"
    MODULE_NAME = "CameraManager"
    spec = importlib.util.spec_from_file_location(MODULE_NAME, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    from CameraManager.CameraManager_MP import CameraManager_MP

# Classes
class HamCam(CameraManager_MP):
    def __init__(self, camera_no=0):
        super(HamCam, self).__init__()
        self._exposure_time_sec = 4
        self._no_of_frames = 10         # adjust to the desired number of frames

        self._device_no = camera_no

        self._dcam = None
        # try:
        self._model = ""
        self._camera_id = ""
        self._camera_version = ""
        self._driver_version = ""
        self._dcamapi_version = ""
        self._camera_series_name = ""
        self._vendor = ""
        self._bus = ""
        self._module_version = ""
        # except Exception as error:
        #     e = f"{dcam.DCAMERR(dcam.Dcamapi.lasterr()).name}"
        #     print(f"Error Encountered: No DCAM_{error} .. '{e}'")

    def __str__(self):
        output_str = super(HamCam, self).__str__()
        return (f'###{self._device_no}: {self._vendor} camera Model : {self._model}// {self._camera_id}// '
                f'Camera Version: {self._camera_version}// Driver Version: {self._driver_version}// Dcamapi Version: {self._dcamapi_version}\n'
                f"{output_str}\n"
                f"Exposure Time = {self.get_exposure_time()*1000} ms\n")

    def Camera_Open(self):
        #
        return self._dcam.dev_open()

    def Camera_Close(self):
        #
        return self._dcam.dev_close()

    def dcam_camera_connect(self):
        #
        self.Camera_Initialize()
        self._dcam = dcam.Dcam(self.get_device_no())
        try:
            self._model = self.get_camera_model()
            self._camera_id = self.get_camera_id()
            self.set_camera_name(f"Ham-1-{self._model}_{self._camera_id}")

            self._camera_version = self._dcam.dev_getstring(dcam.DCAM_IDSTR.CAMERAVERSION)
            self._driver_version = self._dcam.dev_getstring(dcam.DCAM_IDSTR.DRIVERVERSION)
            self._dcamapi_version = self._dcam.dev_getstring(dcam.DCAM_IDSTR.DCAMAPIVERSION)
            self._camera_series_name = self._dcam.dev_getstring(dcam.DCAM_IDSTR.CAMERA_SERIESNAME)
            self._vendor = self._dcam.dev_getstring(dcam.DCAM_IDSTR.VENDOR)
            self._bus = self._dcam.dev_getstring(dcam.DCAM_IDSTR.BUS)
            self._module_version = self._dcam.dev_getstring(dcam.DCAM_IDSTR.MODULEVERSION)
        except Exception as error:
            e = f"{dcam.DCAMERR(dcam.Dcamapi.lasterr()).name}"
            print(f"Error Encountered: No DCAM_{error} .. '{e}'")

    # Hamamatsu Camera Properties
    def get_exposure_time(self):
        #
        return self._exposure_time_sec

    def set_exposure_time(self, ex_time):
        # Set Exposure time in us
        ex_time = ex_time / 1000000
        self._exposure_time_sec = ex_time

    def get_device_no(self):
        #
        return self._device_no

    def get_camera_model(self):
        #
        return self._dcam.dev_getstring(dcam.DCAM_IDSTR.MODEL)

    def get_camera_id(self):
        #
        return self._dcam.dev_getstring(dcam.DCAM_IDSTR.CAMERAID)

    def set_camera_name(self, camera):
        #
        self._camera = f"{camera}"

    # Hamamatsu Camera Capture Functions
    def camera_start_capture(self):
        #
        return self._dcam.cap_start(True)

    def camera_stop_capture(self):
        #
        return self._dcam.cap_stop()

    def camera_capture_status(self):
        #
        return self._dcam.cap_status()

    # def create_settings_dict(self):
    #     """
    #
    #     @return:
    #     """
    #     settings_dict = {"camera": self._camera,
    #                      "image_directory": self._image_directory,
    #                      "thermal_cal": self._thermal_cal,
    #                      "colormap": self._colormap,
    #                      "resize": self._resize,
    #                      "exposure_time": self._exposure_time_sec,
    #                      # "image_processing": self._func_img_proc.__name__
    #                      "Alg_Settings": {}
    #                      }
    #     return settings_dict

    def camera_change_settings(self):
        """

        @param camera:
        @return:
        """
        print("Available commands: 'cmap' to change colormap e.g. \"cmap magma\"\n"
              # "                    'cal' to change the thermal calibration\n"
              # "                    'crop' to crop camera image\n"
              # "                    'e' to change exposure time\n"
              # "                    's' to change image display size\n"
              "                    'ret' to toggle reticle on\n"
              "                    'rec' to toggle recording tiff images to a folder location\n")

        command = input("Type the setting to be changed followed by the value: ")
        command_list = command.split(' ')
        for c in range(len(command_list)):
            if command_list[c] == "cmap":
                # command = input("Colormap Name: ")
                c += 1
                try:
                    self.set_colormap(command_list[c])
                    self.set_color_scale()
                    print(f"Colormap changed to: {self.get_colormap()}")
                except (ValueError, IndexError):
                    self.set_colormap("afmhot")
                    self.set_color_scale()
                    print("Colormap not defined or not available. Setting default colormap.")
            elif command_list[c] == "ret":
                if self.get_reticle_flag():
                    self.set_reticle_flag(False)
                else:
                    self.set_reticle_flag(True)
            elif command_list[c] == "rec":
                c += 1
                try:
                    self.set_record_flag(True)
                    if os.path.isdir(command_list[c]):
                        self.set_image_directory(command_list[c])
                        print(f"Start Recording data to '{self.get_image_directory()}'")
                        # ##################################
                        # print(" initialising RecProc...")
                        # RecProc = ImageProc_MP.ImageProc(self.get_image_queue())
                        # RecProc.daemon = True
                        # RecProc.set_folder_name(Ham_Cam.get_image_directory())
                        # print(" Starting RecProc...")
                        # RecProc.start()
                        # time.sleep(1)
                        # print(" Running RecProc...")
                        # elif not Ham_Cam.get_record_flag() and RecProc is not None:
                        #     RecProc.stop_process()
                        #     RecProc.join(2)
                        #     RecProc.terminate()
                        #     del RecProc
                        #     RecProc = None
                        # ##################################
                    else:
                        print(f"\"{command_list[c]}\" directory not found")
                except IndexError:
                    print("INDEX ERROR: Directory path not defined.")
            # else:
            #     print(f"The following command is not available: {command_list[c]}")
            #     print("Restarting camera with default settings.")

        return 1

    def live_camera_property_change(self, camera):
        msg = self.get_msg_queue().get_nowait()

        if msg[0] == 'h':
            print("Available commands: 'cmap' to change colormap\n"
                  "                    'cal' to change the thermal calibration\n"
                  "                    'crop' to crop camera image\n"                  
                  "                    'e' to change exposure time\n"
                  "                    's' to change image display size\n"
                  "                    'r' to toggle reticle on/off\n"
                  "                    'rec' to toggle recording tiff images to a folder location\n")
        elif msg[0] == 'cmap':
            self.set_colormap(msg[1])
            self.set_color_scale()
            print(f"Colormap changed to: {self.get_colormap()}")
        elif msg[0] == 'cal':
            current_cal = self.get_thermal_Cal()
            self.set_thermal_Cal(msg[1])
            self.set_temp_scale()
            print(f"Thermal calibration changed from {current_cal} and set to {self.get_thermal_Cal()}")
        elif msg[0] == 'crop':
            img_dim = (camera.sensor_height_pixels, camera.sensor_width_pixels)
            if msg[1].__contains__(0):
                self.set_img_crop(img_dim)
                self._crop_flag = False
            else:
                self.set_img_crop(msg[1])
                self._crop_flag = True
            print(f"Image dimension {img_dim} will be cropped to {msg[1]}")
        elif msg[0] == 'e':
            current_ex = camera.exposure_time_us / 1000
            camera.exposure_time_us = int(msg[1])  # set exposure in us
            print(f"Exposure time changed from {current_ex}ms and set to {camera.exposure_time_us / 1000} ms")
        elif msg[0] == 's':
            self.set_resize(msg[1])
            print(f"Image render size change to {self.get_resize()}")
        elif msg[0] == 'r':
            if self.get_reticle_flag():
                self.set_reticle_flag(False)
            else:
                self.set_reticle_flag(True)
        elif msg[0] == 'rec':
            if msg[1] == 0:
                self.set_record_flag(False)
                print(f"Stopped Recording to '{self.get_image_directory()}'")
            else:
                self.set_record_flag(True)
                self.set_image_directory(msg[1])
                print(f"Start Recording data to '{self.get_image_directory()}'")

    def default_img_proc(self, therm_img, pixel, img_color, frame_no, **kwargs):

        img_dim = pixel.shape

        # Frame Image Processing
        # Rotate Frame Anti-Clockwise 90deg
        # therm_img = cv2.rotate(therm_img, cv2.ROTATE_90_COUNTERCLOCKWISE)

        # Generate Thermal Image
        img_temp = Til.generate_temp_map(therm_img, pixel, self._temp_scale)
        image_max = round(float(np.amax(img_temp)), 2)
        img_color = Til.generate_temp_colormap(therm_img, img_color, self.get_color_scale())

        # Add Reticle to image
        if self.get_reticle_flag():
            img_centre = (int(img_color.shape[1] / 2), int(img_color.shape[0] / 2))
            # Vertical Centre Line
            img_color = cv2.line(img_color, (img_centre[0], 0), (img_centre[0], img_dim[0]),
                                 thickness=2, color=(255, 255, 0))
            # Horizontal Centre Line
            img_color = cv2.line(img_color, (0, img_centre[1]), (img_dim[1], img_centre[1]),
                                 thickness=2, color=(255, 255, 0))
            # Reticle Circles
            img_color = cv2.circle(img_color, img_centre, 4, (255, 255, 0), 2)
            img_color = cv2.circle(img_color, img_centre, 100, (255, 255, 0), 2)
            img_color = cv2.circle(img_color, img_centre, 200, (255, 255, 0), 2)

        # Add data to thermal image
        # img_color = cv2.circle(img_temp, (max_index[1], max_index[0]), 6, (255, 0, 0), -1)
        frame_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S_%f')
        text = f"{frame_time.split('_')[0]} || Tmax = {image_max}"
        img_color = cv2.putText(img_color, text, (25, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

        # Record Images to directory as Tiff files
        if self.get_record_flag():  # and frame_no % 2 == 0:
            Til.Save_tiff_Image(therm_img, self.get_image_directory(), f"Image_{frame_time.replace(':', '_')}")
            # if not self.get_image_queue().full():
            #     self.get_image_queue().put_nowait((frame_time, therm_img))

        # Show Processed Image at required size
        img_re = cv2.resize(img_color, (0, 0), fx=self._resize, fy=self._resize, interpolation=cv2.INTER_LINEAR)
        Til.Show_Image("HamCam", f"{self._camera}: Image {frame_no} || fps = {self.get_fps()}", img_re, 1)

        # Add data to Image Queue
        #////////////////////////#

    def camera_live_capture(self):
        #
        if self.camera_start_capture() is not False:
            window_status = 0
            frame_no = 0
            RecProc = None

            # initialise cython code variables
            img_dim = (int(self._dcam.prop_getvalue(dc4.DCAM_IDPROP.IMAGE_HEIGHT)), int(self._dcam.prop_getvalue(dc4.DCAM_IDPROP.IMAGE_WIDTH)))
            print(f"Image dim = {img_dim}")
            pixel = np.zeros((img_dim[0], img_dim[1]), dtype=np.single)
            img_color = np.zeros((img_dim[0], img_dim[1], 3), dtype=int)
            img_color = np.uint8(img_color)

            # Create Settings dict
            # self._settings = self.create_settings_dict()

            # Infinite while loop for live capturing
            frame_timer = time.time_ns()
            while not self._stop_event.is_set() and window_status >= 0:
                try:
                    #
                    if not self.get_msg_queue().empty():
                        self.live_camera_property_change(HamCam)

                    if self._dcam.wait_capevent_frameready(timeout_millisec=1000) is not False:
                        # Get data frame from camera
                        therm_img = self._dcam.buf_getlastframedata()
                        # window_status, data = self

                        # Image Processing
                        # self.default_img_proc(therm_img, pixel, img_color, img_dim, frame_no)
                        self._func_img_proc(therm_img, pixel, img_color, frame_no, camera=self)

                        # Calculate FPS
                        frame_no += 1
                        if frame_no % 10 == 0:
                            self.calculate_fps(frame_timer, 10)
                            frame_timer = time.time_ns()
                            gc.collect()
                            # print(f"FPS = {self.get_fps()} || frame Number = {frame_no} || Image dimensions = {img_color.shape}")
                        # time.sleep(0.05)
                    else:
                        camera_error = self._dcam.lasterr()
                        if camera_error.is_timeout():
                            print("Camera Error: TIMEOUT")
                        else:
                            err = dcam.DCAMERR(camera_error).name
                            print(f"Camera Error: wait_event() fails with error {camera_error}: '{err}'")
                except KeyboardInterrupt:
                    print(f"Keyboard Interrupt: Stopping Live Capture from {self.get_camera_name()}")
                    break
                except Exception as error:
                    print(f"Encountered Error: {error}_{sys.exc_info()[2]}, Image acquisition will stop.")
                    break
            self.camera_stop_capture()

            # Create settings.json
            # self.save_settings_json("settings.json", self.get_settings())
            # print("Created settings.json")
            # print(self.get_settings())
            # if len(self.get_settings().keys()) == 0:
            #     self.save_settings_json("settings.json", self.create_settings_dict())
            #     print("Created settings.json")
            # else:
            #     self.save_settings_json("settings.json", self.get_settings())
            #     print("Updated settings.json")
        else:
            err = dcam.DCAMERR(dcam.Dcamapi.lasterr()).name
            print(f"Camera Error: Dcam.cap_start() fails with error '{err}")
        pass

    # Hamamatsu Camera Temperature Sensor
    def get_sensor_temp(self):
        #
        return self._dcam.prop_getvalue(dc4.DCAM_IDPROP.SENSORTEMPERATURE)

    def get_sensor_cooler_mode(self):
        #
        return self._dcam.prop_getvalue(dc4.DCAM_IDPROP.SENSORCOOLER)

    def get_sensor_cooler_status(self):
        #
        return self._dcam.prop_getvalue(dc4.DCAM_IDPROP.SENSORCOOLERSTATUS)

    def get_sensor_cooler_fan(self):
        #
        return self._dcam.prop_getvalue(dc4.DCAM_IDPROP.SENSORCOOLERFAN)

    def get_sensor_temp_target(self):
        #
        return self._dcam.prop_getvalue(dc4.DCAM_IDPROP.SENSORTEMPERATURETARGET)

    def get_sensor_temp_average(self):
        #
        return self._dcam.prop_getvalue(dc4.DCAM_IDPROP.SENSORTEMPERATURE_AVE)

    def get_sensor_temp_min(self):
        #
        return self._dcam.prop_getvalue(dc4.DCAM_IDPROP.SENSORTEMPERATURE_MIN)

    def get_sensor_temp_max(self):
        #
        return self._dcam.prop_getvalue(dc4.DCAM_IDPROP.SENSORTEMPERATURE_MAX)

    def get_sensor_temp_status(self):
        #
        return self._dcam.prop_getvalue(dc4.DCAM_IDPROP.SENSORTEMPERATURE_STATUS)

    def get_sensor_temp_protect(self):
        #
        return self._dcam.prop_getvalue(dc4.DCAM_IDPROP.SENSORTEMPERATURE_PROTECT)

    def create_settings_dict(self):
        """

        @return:
        """
        settings_dict = super(HamCam, self).create_settings_dict()
        settings_dict["exposure_time_sec"] = self.get_exposure_time()
        settings_dict["reticle_flag"] = self.get_reticle_flag()
        return settings_dict

    # STATIC METHODS
    @staticmethod
    def Camera_Initialize():
        #
        return dcam.Dcamapi.init()

    @staticmethod
    def Camera_Un_Initialize():
        #
        return dcam.Dcamapi.uninit()

    @staticmethod
    def dcam_detect_devices_no():
        """
        Show HAMAMATSU Device List
        @return:
        """
        if dcam.Dcamapi.init() is not False:
            n = dcam.Dcamapi.get_devicecount()
            print(f"Dcam found {n} devices connected")

            for i in range(0, n):
                hcam = dcam.Dcam(i)
                out_str = f"###{i}: "

                model = hcam.dev_getstring(dcam.DCAM_IDSTR.MODEL)
                if model is not False:
                    out_str = out_str + f"Model = {model}"
                else:
                    out_str = out_str + "No DCAM_IDSTR.MODEL"

                cameraID = hcam.dev_getstring(dcam.DCAM_IDSTR.CAMERAID)
                if cameraID is not False:
                    out_str = out_str + f", CAMERA ID = {cameraID}"
                else:
                    out_str = out_str + ", No DCAM_IDSTR.CAMERAID"

                print(f"{out_str}\n")

        else:
            n = -1
            error = dcam.DCAMERR(dcam.Dcamapi.lasterr()).name
            print(f"No Camera Detected-NG: Dcamapi.init() fails with error '{error}'")

        dcam.Dcamapi.uninit()
        return n

    # PROCESS START
    def run(self) -> None:
        # Open Camera and set Properties
        self.dcam_camera_connect()
        print("Hamamatsu Camera Process Starting...")

        if self.Camera_Open() is not False:
            if self._dcam.buf_alloc(3) is not False:
                # Set Exposure Time
                self._dcam.prop_setvalue(dc4.DCAM_IDPROP.EXPOSURETIME, self.get_exposure_time())
                print(f"Exposure Time set = {self._dcam.prop_getvalue(dc4.DCAM_IDPROP.EXPOSURETIME)}s")

                # Start Camera Capture
                self.camera_live_capture()
            else:
                err = dcam.DCAMERR(dcam.Dcamapi.lasterr()).name
                print(f"Camera Error: Dcam.buf_alloc(3) fails with error '{err}'")

            self.Camera_Close()
        else:
            err = dcam.DCAMERR(dcam.Dcamapi.lasterr()).name
            print(f"Camera Error: Dcam.dev_open() fails with error '{err}'")        

            self.Camera_Un_Initialize()
            print("Image acquisition stopped, and Camera un-initialized.")

# MAIN
if __name__ == "__main__":

    # No_HamCam = 1
    # HamCam.dcam_detect_devices_no() crashes python; need more testing
    No_HamCam = HamCam.dcam_detect_devices_no()

    # Set camera running in Polling mode
    mode = 1
    if No_HamCam > 0 and mode == 0:
    
        print("Success!!!")

    # Set camera to Continuous mode
    elif No_HamCam == 1 and mode == 1:

        restart_flag = None
        RecProc = None

        while restart_flag != 0:

            Ham_Cam = HamCam(No_HamCam - 1)
            Ham_Cam.daemon = True

            if os.path.exists("settings.json"):
                settings = HamCam.load_settings_json("settings.json")
                Ham_Cam.set_camera_name(settings["camera"])
                Ham_Cam.set_image_directory(settings["image_directory"])
                Ham_Cam.set_colormap(settings["colormap"])
                Ham_Cam.set_color_scale()
                Ham_Cam.set_resize(settings["resize"])
                # if settings["image_processing"] != "":
                #     Ham_Cam.set_img_proc_func(eval("Ham_Cam." + settings["image_processing"]))
                Ham_Cam.set_exposure_time(settings["exposure_time_sec"]*1000000)
                Ham_Cam.set_thermal_Cal(settings["thermal_cal"])
                Ham_Cam.set_reticle_flag(settings["reticle_flag"])
            else:
                Ham_Cam.set_camera_name("Ham-1")
                Ham_Cam.set_image_directory("")
                Ham_Cam.set_colormap('afmhot')
                Ham_Cam.set_color_scale()
                Ham_Cam.set_resize(0.4)
                Ham_Cam.set_exposure_time(40000)
                Ham_Cam.set_thermal_Cal((213.4, 0.1406, 218.6))         #
                # Ham_Cam.set_thermal_Cal((215.4, 0.154, 261.8))        # North End Camera
                Ham_Cam.set_reticle_flag(False)

            if restart_flag == 1:
                Ham_Cam.camera_change_settings()

            try:
                Ham_Cam.start()
                time.sleep(5)

                # print(f'Exposure time set = {Ham_Cam.get_exposure_time()}s')
                print(Ham_Cam)

                while Ham_Cam.is_alive():
                    # y = input("To Restart Camera press 'r' or type \"Quit\" to end program: ")
                    # if y == "r":
                    #     restart_flag = 1
                    #     print("Stopping Camera...")
                    #     Ham_Cam.stop_process()
                    #     Ham_Cam.join()
                    #     Ham_Cam.terminate()
                    # elif y in ["Quit", "quit", "q", "Q"]:
                    #     restart_flag = 0
                    #     raise KeyboardInterrupt

                    y = input("Input 'h' to get a list of available options, or 'end' to exit program\n"
                              "Type setting to be changed:")
                    if y == "h":
                        Ham_Cam.get_msg_queue().put_nowait((y, 0))
                    elif y == "cmap":
                        val = input("Input colormap name: ")
                        Ham_Cam.get_msg_queue().put_nowait((y, val))
                    elif y == "cal":
                        val = input("Input thermal calibration in the format 'A,B,C': ")
                        cal = val.split(',')
                        cal = (float(cal[0]), float(cal[1]), float(cal[2]))
                        Ham_Cam.get_msg_queue().put_nowait((y, cal))
                    elif y == "e":
                        val = input("Input exposure time in us: ")
                        Ham_Cam.get_msg_queue().put_nowait((y, val))
                    elif y == "s":
                        val = input("Input new image size as a fraction of 1: ")
                        Ham_Cam.get_msg_queue().put_nowait((y, float(val)))
                    elif y == "r":
                        Ham_Cam.get_msg_queue().put_nowait((y, 0))
                    elif y == "rec":
                        if not Ham_Cam.get_record_flag():
                            val = input("Input full directory path to save images:")
                            Ham_Cam.set_record_flag(True)
                            Ham_Cam.get_msg_queue().put_nowait((y, val))
                        else:
                            Ham_Cam.set_record_flag(False)
                            Ham_Cam.get_msg_queue().put_nowait((y, 0))
                    elif y == "end":
                        print("Stopping Process...")
                        Ham_Cam.stop_process()
                        Ham_Cam.join(2)
                        Ham_Cam.terminate()
                    else:
                        print("unrecognized command!!")
                    time.sleep(0.2)
            except IndexError:
                logging.exception("No Cameras found!!")
            except KeyboardInterrupt:
                print(f"Stopping Process...")
                Ham_Cam.stop_process()
                Ham_Cam.join()
                Ham_Cam.terminate()
                del Ham_Cam

    print("Program Completed !!!")
