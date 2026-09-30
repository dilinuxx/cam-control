"""
############
DESCRIPTION:
############

#####
TO DO:
#####
1- Add Message Queue to change properties while camera process is running
2- Test changing colormap while process is running
4- Overlay frame timestamp and max temperature on every image
5- Add logging functionality and remove print statements
#####
BUGS:
#####

"""
import logging
import os
import time
import datetime
import json
import multiprocessing as mp

import cv2
import numpy as np

import ThermalImageLib as Til

# CONSTANTS


# CLASSES
class CameraManager_MP(mp.Process):
    def __init__(self):
        super(CameraManager_MP, self).__init__()
        self._camera = 'Virtual Camera'
        self._image_directory = ''

        self._colormap = 'afmhot'
        self._bit_depth = 16
        self._colormap_scale = 1
        self._thermal_cal = (171.4, 0.1339, 196.2)      # A, B, C
        # Define empty temperature scale
        self._temp_scale = np.zeros((256, 1))
        self.set_temp_scale()
        # Define empty color scale
        self._color_scale = np.zeros((256, 3))
        self.set_color_scale()

        self._resize = 0.5
        self._img_crop = (0, 0)
        self._crop_flag = False
        self._fps = 0
        self._reticle_flag = True
        self._record_flag = False
        self._video_out = ""
        self._settings = {} #self.create_settings_dict()
        self._func_img_proc = self.default_img_proc
        self._msg_queue = mp.Queue(maxsize=2)
        self._image_queue = mp.Queue(maxsize=10)
        self._stop_event = mp.Event()

    def __str__(self):
        return (f"Multiprocessing Camera manager name: {self._camera}\n"
                f"Directory: {self._image_directory}\n"
                f"Colormap : {self._colormap}; Color Scale = {self._colormap_scale}\n"
                f"Thermal Calibration: {self._thermal_cal}\n"
                f"Image Size = {self._resize}")

    def get_camera_name(self):
        #
        return self._camera

    def set_camera_name(self, camera):
        #
        self._camera = camera

    def get_image_directory(self):
        #
        return self._image_directory

    def set_image_directory(self, directory_path: str):
        #
        self._image_directory = directory_path

    def get_colormap(self):
        #
        return self._colormap

    def set_colormap(self, colormap: str):
        #
        self._colormap = colormap

    def get_bit_depth(self):
        #
        return self._bit_depth

    def get_colormap_scale(self):
        # The colormap scale is a power of 2 and determines
        # the number of colors to be generated in the colormap
        return self._colormap_scale

    def set_colormap_scale(self, scale):
        # The colormap scale is a power of 2 and determines
        # the number of colors to be generated in the colormap
        self._colormap_scale = scale

    def get_thermal_Cal(self):
        # Tuple of the format (A, B, C)
        return self._thermal_cal

    def set_thermal_Cal(self, thermal_cal):
        # Tuple of the format (A, B, C)
        self._thermal_cal = thermal_cal

    def get_temp_scale(self):
        #
        return self._temp_scale

    def set_temp_scale(self):
        #
        bits = int(self.get_bit_depth() / self.get_colormap_scale())
        self._temp_scale = Til.generate_temp_scale(bits, self.get_thermal_Cal())

    def get_color_scale(self):
        #
        return self._color_scale

    def set_color_scale(self, norm=""):
        #
        bits = int(self.get_bit_depth() / self.get_colormap_scale())
        if norm == "twoSlope":
            # color_scale = np.arange(0, 2**bits, 1)
            # self._color_scale = Til.generate_color_scale_twoSlope(self.get_colormap(), bits, color_scale, smin=0.001, scenter=0.01)
            self._color_scale = Til.generate_color_scale_twoSlope(self.get_colormap(), bits, self.get_temp_scale(), smin=0.5, scenter=0.6)
        else:
            self._color_scale = Til.generate_color_scale(self.get_colormap(), bits)

    def get_reticle_flag(self):
        #
        return self._reticle_flag

    def set_reticle_flag(self, flag):
        #
        self._reticle_flag = flag

    def get_record_flag(self):
        #
        return self._record_flag

    def set_record_flag(self, flag):
        #
        self._record_flag = flag

    def get_video_out(self):
        #
        return self._video_out

    def set_video_out(self, vid_name='output.avi', codec='divx', fps=10.0, video_res=(800, 800)):
        #
        self._video_out = cv2.VideoWriter(vid_name, cv2.VideoWriter_fourcc(*codec), fps, video_res, True)

    def get_settings(self):
        #
        return self._settings

    def set_settings(self, settings_dict):
        #
        self._settings = settings_dict

    def get_resize(self):
        #
        return self._resize

    def set_resize(self, resize):
        #
        self._resize = resize

    def get_img_crop(self):
        #
        return self._img_crop

    def set_img_crop(self, crop):
        #
        self._img_crop = crop

    # def get_crop_flag(self):
    #     #
    #     return self._crop_flag

    def get_fps(self):
        #
        return self._fps

    def calculate_fps(self, start, n=1):
        """

        @param start:
        @param n:
        @return:
        """
        freq = round(1000000000*n/(time.time_ns() - start), 2)
        self._fps = freq

    def get_msg_queue(self):
        """

        """
        return self._msg_queue

    def get_image_queue(self):
        """

        """
        return self._image_queue

    def get_img_proc_func(self):
        #
        return self._func_img_proc

    def set_img_proc_func(self, func):
        #
        self._func_img_proc = func

    def capture_Video(self, img_src, C_frames, frame_no=200):
        """
        Image_2022-10-20 11_05_22_757613.tif
        :return:
        """
        VideoOut = self.get_video_out()
        if (C_frames < frame_no) or (frame_no == -1):
            VideoOut.write(img_src)
            # print(f'Frame No.: {CaptureFrames}')
        else:
            VideoOut.release()
            # print("<--STOP RECORDING-->")

        C_frames += 1

        return C_frames

    def default_img_proc(self, therm_img, pixel, img_color, frame_no, **kwargs):
        """

        @return:
        """
        # Add image processing algorithm
        # ...

        # Create temperature image with colormap
        # therm_img, image_max, max_index, image_min, min_index = Til.CurveFitting_Thermal_Image(self._thermal_cal, image)
        #
        # # final = cv.normalize(img, norm, 0, 255, cv.NORM_MINMAX)
        # therm_img = cv2.normalize(therm_img, np.zeros(therm_img.shape), 0, 1, cv2.NORM_MINMAX)
        # # therm_img = therm_img/image_max
        #
        # therm_img = Til.Apply_Colormap(COLORMAP, therm_img)

        # Generate thermal image and colormap using cython
        img_temp = Til.generate_temp_map(therm_img, pixel, self.get_temp_scale())
        image_max = round(float(np.amax(img_temp)), 2)
        ##
        img_color = Til.generate_temp_colormap(therm_img, img_color, self.get_color_scale())

        # Sharpen temperature image
        # therm_img = Til.Sharpen_Image(therm_img)

        # Add data to thermal image
        # img_color = cv2.circle(img_temp, (max_index[1], max_index[0]), 6, (255, 0, 0), -1)
        frame_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S_%f')
        text = f"{frame_time.split('_')[0]} || Tmax = {image_max}"
        img_color = cv2.putText(img_color, text, (25, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

        # Resize & Show image
        img_re = cv2.resize(img_color, (0, 0), fx=self._resize, fy=self._resize, interpolation=cv2.INTER_LINEAR)
        # Til.Show_Image("ThermImage", "Thermal Image", img_re, 1)
        Til.Show_Image("HamCam", f"{self._camera}: Image {frame_no + 1} || fps = {self.get_fps()}", img_re, 1)
        # time.sleep(0.2)

        # Add Processed image to Queue
        # ...

    def stop_process(self):
        """

        """
        self._stop_event.set()

    def create_image_list(self):
        """

        @return:
        """
        sampleList = os.listdir(self._image_directory)
        return sampleList

    def create_settings_dict(self):
        """

        @return:
        """
        settings_dict = {"camera": self._camera,
                         "image_directory": self._image_directory,
                         "thermal_cal": self.get_thermal_Cal(),
                         "colormap": self.get_colormap(),
                         "resize": self.get_resize(),
                         # "image_processing": self._func_img_proc.__name__
                         "Alg_Settings": {}
                         }
        return settings_dict

    @staticmethod
    def save_settings_json(filename, settings):
        """

        @return:
        """
        # Object serialization
        json_object = json.dumps(settings, indent=4)
        with open(filename, "w") as jsonfile:
            jsonfile.write(json_object)

    @staticmethod
    def load_settings_json(filename):
        """

        @return:
        """
        with open(filename, "r") as openfile:
            # Reading from json file
            json_dict = json.load(openfile)

        return json_dict

    @staticmethod
    def live_settings_change(Camera):
        """

        @return:
        """
        y = input("Input 'h' to get a list of available options, or 'end' to exit program\n"
                  "Type setting to be changed:")
        if y == "h":
            Camera.get_msg_queue().put_nowait((y, 0))
        elif y == "cmap":
            val = input("Input colormap name: ")
            Camera.get_msg_queue().put_nowait((y, val))
        elif y == "cal":
            val = input("Input thermal calibration in the format 'A,B,C': ")
            cal = val.split(',')
            cal = (float(cal[0]), float(cal[1]), float(cal[2]))
            Camera.get_msg_queue().put_nowait((y, cal))
        elif y == "crop":
            val = input("Input required image size in the format 'height,width':")
            crop = val.split(',')
            crop = (int(crop[0]), int(crop[1]))
            Camera.get_msg_queue().put_nowait((y, crop))
        elif y == "e":
            val = input("Input exposure time in us: ")
            Camera.get_msg_queue().put_nowait((y, val))
        elif y == "s":
            val = input("Input new image size as a fraction of 1: ")
            Camera.get_msg_queue().put_nowait((y, float(val)))
        elif y == "r":
            Camera.get_msg_queue().put_nowait((y, 0))
        elif y == "rec":
            if not Camera.get_record_flag():
                if Camera.get_image_directory() == '':
                    val = input("Input full directory path to save images:")
                else:
                    val = Camera.get_image_directory()
                Camera.set_record_flag(True)
                Camera.get_msg_queue().put_nowait((y, val))
            else:
                Camera.set_record_flag(False)
                Camera.get_msg_queue().put_nowait((y, 0))
        elif y == "end":
            print("Stopping Process...")
            Camera.stop_process()
            Camera.join(2)
            Camera.terminate()
        else:
            print("unrecognized command!!")

    def run(self) -> None:
        print(f"{self._camera} Manager Process Starting...")

        # Create Thermal image colormap
        # COLORMAP = Til.Create_ColorMap(self._colormap, no_Bits=self._bit_depth, scale=self._colormap_scale)

        # Generate Image list from directory
        image_list = self.create_image_list()

        # initialise cython code variables
        img_dim = cv2.imread(f"{self._image_directory}/{image_list[0]}", cv2.IMREAD_ANYDEPTH).shape
        print(f"Image dim = {img_dim}")
        pixel = np.zeros((img_dim[0], img_dim[1]), dtype=np.single)
        img_color = np.zeros((img_dim[0], img_dim[1], 3), dtype=int)
        img_color = np.uint8(img_color)

        # Create Settings dict
        # self._settings = self.create_settings_dict()

        # Itterate through image list
        image_id = 0
        while image_id < len(image_list) and not self._stop_event.is_set():
            process_timer = time.time_ns()

            # print(f"Image ID: {image_list[image_id]} || Queue Length: {self._image_queue.qsize()}")

            # Read Raw image
            therm_img = cv2.imread(f"{self._image_directory}/{image_list[image_id]}", cv2.IMREAD_ANYDEPTH)

            # Image Processing
            # self._func_img_proc(therm_img, pixel, img_color, image_id)
            self._func_img_proc(therm_img, pixel, img_color, image_id, camera=self)

            # Calculate FPS
            self.calculate_fps(process_timer)
            # print(f"FPS = {self._fps}")

            image_id += 1
        print(f"Total image processed = {image_id}")

        # Create settings.json
        # print(self.get_settings())
        if len(self.get_settings().keys()) == 0:
            self.save_settings_json("settings.json", self.create_settings_dict())
            print("Created settings.json")
        else:
            self.save_settings_json("settings.json", self.get_settings())
            print("Updated settings.json")

        print(f"Process Stopping!!!")

# MAIN
if __name__ == "__main__":
    # directory = "D:/PyrOptik/Python/CameraWebPlatform/Samples"
    # directory = r"E:\StrandEnd\South"
    # directory = r"E:\StrandEnd_11-10-22"
    directory = r"D:\PyrOptik\Desulf\21360"

    virtual_Cam = CameraManager_MP()
    virtual_Cam.daemon = True
    virtual_Cam.set_image_directory(directory)
    virtual_Cam.set_colormap('afmhot')
    virtual_Cam.set_color_scale()
    virtual_Cam.set_resize(0.4)

    try:
        virtual_Cam.start()
        time.sleep(0.5)

        image_no = 0
        # image_qu = virtual_Cam.get_image_queue()
        while virtual_Cam.is_alive():
            time.sleep(0.1)

            y = input("End Process (y/n): ")
            if y in ["y", "Y"]:
                print("stopping Process...")
                virtual_Cam.stop_process()
                virtual_Cam.join(2)
                virtual_Cam.terminate()
    except IndexError:
        logging.exception("No Cameras found!!")
    except KeyboardInterrupt:
        print(f"Stopping Process...")
        virtual_Cam.stop_process()
        virtual_Cam.join(2)
        virtual_Cam.terminate()
        del virtual_Cam

    print("Program Terminated!!!")