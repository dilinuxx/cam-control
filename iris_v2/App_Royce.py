"""
############
DESCRIPTION:
############

#####
TO DO:
#####


#####
BUGS:
#####



"""
import os
import sys
import traceback
import argparse
import importlib
import logging
import time
import datetime
import json
import dataclasses
from dataclasses import dataclass, field

import matplotlib as mpl
import numpy as np
import pandas as pd
import cv2

import nidaqmx
import ThermalImageLib as Til
from CameraManager.CameraManager_MP import CameraManager_MP

try:
    from Hamamatsu.Hamamatsu import HamCam
except ImportError:
    # absolute_path_to_file_directory = os.path.abspath(os.path.join(path, os.pardir))
    MODULE_PATH = "Hamamatsu/__init__.py"
    # print(MODULE_PATH)
    MODULE_NAME = "Hamamatsu"
    spec = importlib.util.spec_from_file_location(MODULE_NAME, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    from Hamamatsu.Hamamatsu import HamCam

# PARSER
parser = argparse.ArgumentParser()

# Application specific parse arguments
parser.add_argument("-s", "--settings", help="Define path of script settings file", type=str)
parser.add_argument("-i", "--input", help="Define path of input folder", type=str)
parser.add_argument("-o", "--output", help="Define path of output folder", type=str)
parser.add_argument("-c", "--camera", help="0: No Camera, 1: Hamamatsu Camera", type=int)

# Standard parse arguments
parser.add_argument("-v", "--verbose", action="store_true", help="Print complete output")
parser.add_argument("-q", "--quite", action="store_true", help="Print concise output")

args = parser.parse_args()


# Classes
# Settings Dataclass
@dataclass
class AlgSettings:
    settings_file: str = "./Royce_Settings.json"

    # I/O Settings
    input_Folder: str = " "
    output_Folder: str = " "
    record_fps: int = 2

    # Camera Settings
    camera: bool = False
    Cam_Exposure_us: int = 5000
    Thermal_Cal: tuple = (215.4, 0.154, 261.8)
    ColorMap: str = "afmhot"

    # Display Settings
    Display_Size: float = 0.45
    bright: int = 1

    # NI-DAQ Settings
    niDAQ: int = 0
    # Channel_List: list[str] = field(default_factory=list)
    Channels: tuple = ("Dev2/ai0", "Dev2/ai1")
    Channels_dict: dict = field(default_factory=dict)
    Cal_Folder: str = "./"
    Detector_Si_spot_size_mm: float = 5
    Detector_InGa_spot_size_mm: float = 8

    # CTP Head Settings
    rows: int = 2
    cols: int = 50
    laser_offset_um: float = 127
    laser_connected: tuple = (20, 30, 40)

    # Comms Settings
    Serial_Port: str = ""
    baud_rate: int = 9600
    # stop_bits: int = 1
    # timeout: int = 0

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

    def map_dict(self, settings_dict):
        for key, val in settings_dict.items():
            attr_type = type(getattr(self, key))
            self.__setattr__(key, attr_type(val))

##############################################################################


# CONSTANTS
# IMG_Directory = " "
IMG_Directory = r"D:\PyrOptik\Desulf\21360"

# GLOBAL VARIABLES
# Initialize Alg_Settings instance
Alg = AlgSettings()

# Declare Camera Process
Royce_Cam = CameraManager_MP()


# METHODS
def royce_img_proc(therm_img, pixel, img_color, frame_no, **kwargs):
    """

    @param therm_img:
    @param pixel:
    @param img_color:
    @param frame_no:
    @return:
    """
    # global Royce_Cam
    # global Alg

    cam_obj = kwargs['camera']
    # Royce_Cam = kwargs['camera']
    # cam_obj = Royce_Cam

    # Time single algorithm run
    process_timer = time.time_ns()

    # Define image dimension (cols, rows)
    img_dim = pixel.shape

    # Rotate Frame
    # therm_img = cv2. rotate(therm_img, cv2.ROTATE_90_COUNTERCLOCKWISE)

    # Generate thermal image & colormap using TIL
    img_temp,  img_color = therm_img_proc(cam_obj, therm_img, pixel, img_color, brightness=cam_obj.get_settings().bright)
    image_max = round(float(np.amax(img_temp)), 2)

    # Read NI-DAQ Channels
    if cam_obj.get_settings().niDAQ > 0:
        for ch in cam_obj.get_settings().Channels:
            sample = ni_ai_read(ch)
            # print(f"Channel: {ch}, Sample = {sample}")

    # Add Data to thermal color image
    # img_color = cv2.circle(img_temp, (max_index[1], max_index[0]), 6, (255, 0, 0), -1)
    frame_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S_%f')
    text = f"{frame_time.split('_')[0]} || Tmax = {image_max}"
    img_color = cv2.putText(img_color, text, (25, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

    # Add Reticle to image

    # Record images to directory as Tiff files
    if cam_obj.get_record_flag() and frame_no % cam_obj.get_settings().record_fps == 0:
        # print(f"Saved Frame no: {frame_no} ")
        Til.Save_tiff_Image(therm_img, cam_obj.get_image_directory(), f"Image_{frame_time.replace(':', '_')}")
        # if not self.get_image_queue().full():
        #     self.get_image_queue().put_nowait((frame_time, therm_img))

    # Show Processed Image at required size
    display_size = cam_obj.get_resize()
    img_resized = cv2.resize(img_color, (0, 0), fx=display_size, fy=display_size, interpolation=cv2.INTER_LINEAR)
    Til.Show_Image("HamCam", f"{cam_obj.get_camera_name()}: Image {frame_no} || "
                             f"fps = {cam_obj.get_fps()}", img_resized, 1)

    # Calculate FPS
    cam_obj.calculate_fps(process_timer)
    # time.sleep(0.1)

    return process_timer


def therm_img_proc(camera, therm_img, pixel, img_color, brightness=1):
    """
    Process Raw camera images to produce temperature and color images
    @param camera:
    @param therm_img:
    @param pixel:
    @param img_color:
    @param brightness:
    @return:
    """
    # Generate Thermal Image
    img_temp = Til.generate_temp_map(therm_img, pixel, camera.get_temp_scale())
    bits = Royce_Cam.get_bit_depth()
    # print(f"Brightness: {brightness}")
    if brightness != 1:
        img = therm_img
        img[therm_img > int((2**bits-1)/brightness)] = (2**bits)-1  # 65535
        img = img * brightness
    else:
        img = therm_img

    # Generate Color Image
    img_color = Til.generate_temp_colormap(img, img_color, camera.get_color_scale())

    return img_temp, img_color


def ni_ai_read(channel_name: str, n_samples: int = 1):
    """
    Read n samples from NIDAQ channel one time
    @param channel_name:
    @param n_samples:
    @return:
    """
    with nidaqmx.Task() as task:
        task.ai_channels.add_ai_voltage_chan(channel_name, terminal_config=nidaqmx.constants.TerminalConfiguration.RSE)
        return task.read(number_of_samples_per_channel=n_samples)


# MAIN
if __name__ == "__main__":
    # Read Settings File if Available & initialize variables
    if os.path.isfile(Alg.settings_file):
        print(f"Settings file found.")
        alg_dict = Alg.load_settings_json(Alg.settings_file)
        if alg_dict['Channels_dict'] == {}:
            alg_dict['Channels_dict']['Det-1'] = ("f-2", "Dev2/ai0", "")
        Alg.map_dict(alg_dict)
        print(f"Settings Loaded")
        print(f"Settings: {Alg}")
    else:
        print("No Settings file found, using defaults!!")

    # Override settings with Parser args
    # print(f"Args: {args}")

    # Ask user for settings change if required

    # Initialize Comms Interface

    # Initialize NI_DAQ Channels

    # Initialize camera
    # Detect if camera is available
    if Alg.camera:
        No_HamCam = HamCam.dcam_detect_devices_no()
    else:
        No_HamCam = -1
        if Alg.input_Folder != "":
            IMG_Directory = rf"{Alg.input_Folder}"
        else:
            print("Program set to use images from disk, and no Input Folder is defined!!!")
            print("Update settings and restart program")
            print("program shutting down...")
            sys.exit()

    # Royce_Cam = CameraManager_MP()
    Royce_Cam.daemon = True
    if No_HamCam < 0:
        Royce_Cam.set_image_directory(IMG_Directory)
    else:
        Royce_Cam = HamCam(No_HamCam - 1)
        Royce_Cam.set_exposure_time(Alg.Cam_Exposure_us)

    Royce_Cam.set_thermal_Cal(Alg.Thermal_Cal)
    Royce_Cam.set_temp_scale()

    Royce_Cam.set_colormap(Alg.ColorMap)
    Royce_Cam.set_color_scale()
    Royce_Cam.set_resize(Alg.Display_Size)
    Royce_Cam.set_settings(Alg)
    Royce_Cam.set_image_directory(Alg.output_Folder)

    # Define Image processing function to be used by algorithm
    Royce_Cam._func_img_proc = royce_img_proc

    # print(Royce_Cam.get_settings())
    print(" ")

    try:
        Royce_Cam.start()
        time.sleep(2)

        # Program Loop
        while Royce_Cam.is_alive():
            time.sleep(2)
            # Ask for restart or quit
            if No_HamCam < 0:
                y = input("To Quit type \"Quit\", \"q\", \"Q\": ")
            else:
                y = input("To change settings type \"s\". To Quit type \"Quit\", \"q\", \"Q\": ")

            if y in ["Quit", "quit", "q", "Q"]:
                raise KeyboardInterrupt
            elif y in ["s"]:
                Royce_Cam.live_settings_change(Royce_Cam)

    except IndexError:
        logging.exception("No Cameras found!!")
    except KeyboardInterrupt:
        print(f"Stopping Process...")
        Royce_Cam.stop_process()
        Royce_Cam.join(2)
        Royce_Cam.terminate()
        del Royce_Cam

    cv2.destroyAllWindows()

    # On Exit save settings to settings file
    print(f"Saving Settings to {Alg.settings_file}")
    Alg.save_settings_json(Alg.settings_file, dataclasses.asdict(Alg))
    print("Program Terminated!!")


