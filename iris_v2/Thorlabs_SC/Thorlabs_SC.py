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
4- Overlay frame timestamp and max temperature on every image
5- Add logging functionality and remove print statements
#####
BUGS:
#####

"""
import logging

try:
    # if on Windows, use the provided setup script to add the DLLs folder to the PATH
    from windows_setup import configure_path

    configure_path()
except ImportError:
    configure_path = None

import time
import datetime

import numpy as np
import cv2

import sys
import traceback
import importlib

try:
    import ThermalImageLib as Til
except ImportError:
    MODULE_PATH = "ThermalImageLib/__init__.py"
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

from thorlabs_tsi_sdk.tl_camera import TLCameraSDK, TLCamera, Frame


# import thorlabs_tsi_sdk.tl_camera_enums
# from thorlabs_tsi_sdk.tl_mono_to_color_processor import MonoToColorProcessorSDK

# CLASSES
class ThorCam(CameraManager_MP):
    def __init__(self):
        super(ThorCam, self).__init__()
        # self._tlsdk = TLCameraSDK()
        self._exposure_time_us = 10000
        self._no_of_frames = 10  # adjust to the desired number of frames

    def __str__(self):
        output_str = super(ThorCam, self).__str__()
        return (f"{output_str} \n"
                f"Exposure time = {self._exposure_time_us / 1000} ms")

    def get_tlsdk(self):
        #
        return self.get_tlsdk()

    def get_exposure_time(self):
        #
        return self._exposure_time_us

    def set_exposure_time(self, exposure_time):
        #
        self._exposure_time_us = exposure_time

    def set_no_of_frames(self, frame_no):
        #
        self._no_of_frames = frame_no

    @staticmethod
    def detect_cameras(TLsdk):
        """

        @return:
        """
        available_cameras = TLsdk.discover_available_cameras()
        if len(available_cameras) < 1:
            print("NO CAMERAS DETECTED!!")

        return available_cameras

    def display_thermal_image(self, cam_frame, cm):
        """
        OBSOLETE
        @param cam_frame:
        @param cm:
        @return:
        """
        image = cam_frame.image_buffer
        # Create temperature image
        therm_img, image_max, max_index, image_min, min_index = Til.CurveFitting_Thermal_Image(self.get_thermal_Cal(), image)
        therm_img = Til.Apply_Colormap(cm, therm_img)
        # Show image using CV2
        Til.Show_Image("ThorCam", f"Image {cam_frame.frame_count}", therm_img, 1)
        # Til.Show_Image("ThorCam", f"Image {frame.frame_count}", image, 1)

    @staticmethod
    def init_image_out(dim):
        """

        @param dim:
        @return:
        """
        pixel = np.zeros(dim, dtype=np.single)
        img_color = np.zeros((dim[0], dim[1], 3), dtype=int)
        img_color = np.uint8(img_color)

        return pixel, img_color

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

    def poll_camera(self, TLsdk, camera, roi=()):

        with TLsdk.open_camera(camera) as thorCam:
            thorCam.exposure_time_us = self._exposure_time_us  # set exposure in us
            print(f"Exposure time set to {thorCam.exposure_time_us / 1000} ms")
            thorCam.frames_per_trigger_zero_for_unlimited = 0  # start camera in continuous mode
            thorCam.image_poll_timeout_ms = 1000  # 1 second polling timeout

            """
            Set camera roi if required
            """
            old_roi = thorCam.roi  # store the current camera roi
            if roi != ():
                thorCam.roi = roi  # roi = (100, 100, 600, 600) => set roi to be at origin point (100, 100) with a width & height of 500

            thorCam.arm(2)
            thorCam.issue_software_trigger()

            for i in range(self._no_of_frames):
                frame = thorCam.get_pending_frame_or_null()
                if frame is not None:
                    print(f"frame #{frame.frame_count} received!")
                    # frame.image_buffer

                    image_buffer_copy = np.copy(frame.image_buffer)
                    Til.Show_Image("ThorCam", f"Image {frame.frame_count}", image_buffer_copy, 0)
                else:
                    print(f"timeout reached during polling, function terminating..")
                    break

            thorCam.disarm()
            thorCam.roi = old_roi  # reset the roi back to the original roi

    def run(self) -> None:
        print("Camera process Starting...")

        with TLCameraSDK() as TLsdk:
            available_cameras = ThorCam.detect_cameras(TLsdk)

            with TLsdk.open_camera(available_cameras[0]) as thorCam:
                # Open & Setup camera
                thorCam.exposure_time_us = self._exposure_time_us  # set exposure in us
                print(f"Exposure time set to {thorCam.exposure_time_us / 1000} ms")
                thorCam.frames_per_trigger_zero_for_unlimited = 0  # start camera in continuous mode
                # thorCam.image_poll_timeout_ms = 1000

                # initialise cython code variables
                img_dim = (thorCam.sensor_height_pixels, thorCam.sensor_width_pixels)
                pixel, img_color = self.init_image_out(img_dim)
                img_centre = (int(img_color.shape[1] / 2), int(img_color.shape[0] / 2))

                # Initialize Camera
                thorCam.arm(2)
                # Issue Trigger to camera
                thorCam.issue_software_trigger()

                # Infinite while loop for live capturing
                frame_timer = time.time_ns()
                while not self._stop_event.is_set():
                    try:
                        #
                        if not self.get_msg_queue().empty():
                            self.live_camera_property_change(thorCam)

                        # Get new frame data from camera
                        frame = thorCam.get_pending_frame_or_null()
                        if self.get_image_queue().full():
                            print(f"Dropped Frame {frame.frame_count}!!")
                            pass
                        elif frame is not None:
                            # self.get_image_queue().put_nowait(frame)
                            # therm_img, image_max, max_index, image_min, min_index = Til.CurveFitting_Thermal_Image(
                            #     self.get_thermal_Cal(), frame.image_buffer)
                            ##
                            # Get data frame from camera
                            therm_img = frame.image_buffer

                            # Crop Image
                            if self._crop_flag:
                                img_crop = self.get_img_crop()
                                therm_img = therm_img[(img_centre[1]-img_crop[0]):(img_centre[1]+img_crop[0]),
                                            (img_centre[0]-img_crop[1]):(img_centre[0]+img_crop[1])]
                                pixel, img_color = self.init_image_out(therm_img.shape)
                                img_centre = (int(img_color.shape[1] / 2), int(img_color.shape[0] / 2))

                            # Generate Thermal Image
                            img_temp = Til.generate_temp_map(therm_img, pixel, self._temp_scale)
                            image_max = round(float(np.amax(img_temp)), 2)
                            ##
                            # self.get_image_queue().put_nowait(therm_img)
                            ##
                            img_color = Til.generate_temp_colormap(therm_img, img_color, self.get_color_scale())

                            # Frame Image Processing

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
                            frame_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S_%f')
                            text = f"{frame_time.split('_')[0]} || Tmax = {image_max}"
                            img_color = cv2.putText(img_color, text, (25, 50), cv2.FONT_HERSHEY_SIMPLEX, 1,
                                                    (0, 255, 0), 2, cv2.LINE_AA)

                            # Record Images to directory as Tiff files
                            if self.get_record_flag(): # and frame.frame_count % 3 == 0:
                                Til.Save_tiff_Image(therm_img, self.get_image_directory(), f"Image_{frame_time.replace(':', '_')}")

                            # Show Processed Image at required size
                            img_re = cv2.resize(img_color, (0, 0), fx=self._resize, fy=self._resize, interpolation=cv2.INTER_LINEAR)
                            Til.Show_Image("ThorCam", f"{self.get_camera_name()}: Image {frame.frame_count} || fps = {self.get_fps()}", img_re, 1)

                            # Add data to Image Queue

                            # Calculate FPS
                            if frame.frame_count % 10 == 0:
                                self.calculate_fps(frame_timer, 10)
                                frame_timer = time.time_ns()
                                # print(f"FPS = {self.get_fps()} || Frame Number = {frame.frame_count} || Image dimensions = {therm_img.shape}")
                            # time.sleep(0.1)
                    except KeyboardInterrupt:
                        print("Keyboard Interrupt: Stopping live Capture")
                        break
                    except Exception as error:
                        print(f"Encountered error: {error} || {traceback.format_exc()}, image acquisition will stop.")
                        break

        print("Image acquisition has stopped")


# MAIN
if __name__ == "__main__":

    # Get camera details
    with TLCameraSDK() as sdk:
        cameras = ThorCam.detect_cameras(sdk)
        if cameras:
            print(cameras)
            with sdk.open_camera(cameras[0]) as cam:
                print(f"Camera name: {cam.name} \n"
                      f"Model: {cam.model} \n"
                      f"Serial No. {cam.serial_number}\n"
                      f"Bit Depth: {cam.bit_depth} \n"
                      f"Sensor Type: {cam.camera_sensor_type}\n"
                      f"Sensor Size: ({cam.sensor_width_pixels}, {cam.sensor_height_pixels})")
        else:
            print("Program terminating...")
            sys.exit()

    # Set camera running in Polling mode
    mode = 1
    if mode == 0:
        Camera = ThorCam()
        with TLCameraSDK() as sdk:
            cameras = ThorCam.detect_cameras(sdk)

            if cameras:
                print(f"Available Cameras: {cameras}")

                Camera.set_camera_name(f"Thorlabs-{cameras[0]}")
                Camera.set_resize(0.5)
                Camera.set_no_of_frames(5)

                print(Camera)

                Camera.poll_camera(sdk, cameras[0])
                # Camera.poll_camera(sdk, cameras[0], (100, 100, 600, 600))

        del Camera
        print("Success!!!")

    # Set camera to Continuous mode
    elif mode == 1:

        status = 1

        # Thor_Cam = ThorCam()
        # Thor_Cam.daemon = True
        # Thor_Cam.set_camera_name(f"ThorCam_{cameras[0]}")
        # Thor_Cam.set_image_directory("")
        # Thor_Cam.set_colormap('afmhot')
        # Thor_Cam.set_color_scale()
        # Thor_Cam.set_resize(0.6)
        # Thor_Cam.set_exposure_time(5000)

        # while status != 0:

        Thor_Cam = ThorCam()
        Thor_Cam.daemon = True
        Thor_Cam.set_camera_name(f"ThorCam_{cameras[0]}")
        Thor_Cam.set_image_directory("")
        Thor_Cam.set_colormap('afmhot')
        Thor_Cam.set_color_scale()
        Thor_Cam.set_resize(0.6)
        Thor_Cam.set_exposure_time(5000)

        try:
            Thor_Cam.start()
            time.sleep(2)

            while Thor_Cam.is_alive():
                # process_timer = time.time_ns()
                # Image_Q = Thor_Cam.get_image_queue()
                # if not Image_Q.empty():
                #     frame = Image_Q.get_nowait()
                #     # image = frame.image_buffer
                #     # Create temperature image
                #     # therm_img, image_max, max_index, image_min, min_index = Til.CurveFitting_Thermal_Image(
                #     #     Thor_Cam.get_thermal_Cal(), image)
                #     therm_img = Til.Apply_Colormap(COLORMAP, frame)
                #     # Show image using CV2
                #     Til.Show_Image("ThorCam", f"Image {0}", therm_img, 1)
                #     # Til.Show_Image("ThorCam", f"Image {frame.frame_count}", image, 1)
                #
                #     Thor_Cam.calculate_fps(process_timer)
                #     print(f"FPS = {Thor_Cam.get_fps()}")

                Thor_Cam.live_settings_change(Thor_Cam)
                # Sleep to allow the main process to communicate the setting change to the camera process
                time.sleep(0.2)
        except IndexError:
            logging.exception("No Cameras found!!")
        except KeyboardInterrupt:
            print(f"Stopping Process...")
            Thor_Cam.stop_process()
            Thor_Cam.join(2)
            Thor_Cam.terminate()
            del Thor_Cam

        print("Program Completed !!!")
