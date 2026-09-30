"""
############
DESCRIPTION:
############

Shared Folder: \\ptbssfs1\desulph\videos

{Unit name}_{date}_{StartTime}_{EndTime}_{Skim %}_{Max temp at the end of skim}
Example:
NIDS_01012023_174030_175015_93_1315

#####
TO DO:
#####
1-
#####
BUGS:
#####

"""
import os
import sys, traceback
import importlib
import logging
import time
import datetime
import dataclasses
import loguru
import multiprocessing as mp
from collections import deque

import cv2
import numpy as np
import pandas as pd
from scipy import stats
from matplotlib import pyplot as plt

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
    # import Hamamatsu.dcamapi4 as dc4
    # import Hamamatsu.dcam as dcam
    from Hamamatsu.Hamamatsu import HamCam

# CONSTANTS
UNIT_NAME = "NIDS"
VID_SIZE = 0.5
FPS = 10.0
FOURCC = cv2.VideoWriter_fourcc(*'mp4v')
DIRECTORY = r"D:\PyrOptik\Desulf"
VIDEOFILE = DIRECTORY + r"\output.avi"
IMAGE_FOLDER = "" # r"D:\PyrOptik\Desulf\Images"
IMG_FREQ = 3

# GLOBALS
# Set Test image folder
directory = r"D:\PyrOptik\Desulf\21362"
# directory = r"E:\DesulfTest-1"  #r"E:\Video_5ms"

# Video flag
vid_record_flag = False
rec_count = 0

# Define Video width & height
# height, width = 2048, 2048
video_res = (int(2048 * VID_SIZE), int(2048 * VID_SIZE))

# Define Video & Statistical Analysis ROI
def_roi = (350, 1000, 200, 1800)

# Define display brightness
bright = 6

# Define ROI threshold to start and end video recording
roi_thresh = 1
roi_mean = deque(maxlen=10)

# Video Name Variables
vid_date = ""
start_time = ""
finish_time = ""

# Statistical Variables
image_max = 0
st_mean = 0
st_std = 0
st_MSE = 0
overlay = np.zeros((10, 10, 3))
stats_df = pd.DataFrame(columns=['Frame', 'T_Max', 'Mean', 'Std', 'MSE', 'TSE', 'Cost'])
mu_target = 0
std_target = 30

# Initialize Image Queue
desulf_queue = mp.Queue(maxsize=30)

# Detect if camera is available
No_HamCam = HamCam.dcam_detect_devices_no()

# Initialize CameraManager
Desulf_Cam = CameraManager_MP()
# Detect Hamamatsu Camera
# No_HamCam = HamCam.dcam_detect_devices_no()
# Desulf_Cam = HamCam(No_HamCam-1)
Desulf_Cam.daemon = True
Desulf_Cam.set_image_directory(directory)

# Desulf_Cam.set_exposure_time(5000)
Desulf_Cam.set_thermal_Cal((215.4, 0.154, 261.8))
Desulf_Cam.set_temp_scale()

Desulf_Cam.set_colormap('afmhot')
Desulf_Cam.set_color_scale()
# Desulf_Cam.set_color_scale(norm="twoSlope")
Desulf_Cam.set_resize(0.45)


# CLASSES

# FUNCTIONS
def name_vid_file(date, start, end):
    """

    @return:
    """
    oldname = VIDEOFILE

    percent_Skim = 100
    newname = DIRECTORY + fr"\{UNIT_NAME}_{date}_{start}_{end}_{percent_Skim}_9999.avi"

    os.rename(oldname, newname)


def desulf_img_proc(therm_img, pixel, img_color, frame_no, **kwargs):
    """

    @return:
    """
    global st_mean
    global st_std
    global st_MSE
    global overlay
    global image_max

    process_timer = time.time_ns()

    # Define image dimension (cols, rows)
    img_dim = pixel.shape

    # Rotate Frame Anti-Clockwise 90deg
    # therm_img = cv2.rotate(therm_img, cv2.ROTATE_90_COUNTERCLOCKWISE)

    # Generate thermal image and colormap using cython
    img_temp, img_color = therm_img_proc(Desulf_Cam, therm_img, pixel, img_color, brightness=bright)

    # Statistical Analysis if recording; Fit Gaussian model to temp histogram & calculate MSE
    if vid_record_flag and rec_count % 10 == 0:
        # fun_time = time.time()
        image_max, st_mean, st_std, st_MSE, overlay = stats_analysis(img_temp, temp_thresh=1000, bin_no=128)
        # print(f"{rec_count}--> {(time.time()-fun_time)}")

    # Add Reticle to image

    # Add data to thermal image
    # img_color = cv2.circle(img_temp, (max_index[1], max_index[0]), 6, (255, 0, 0), -1)
    frame_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S_%f')
    text = f"{frame_time.split('_')[0]} || Tmax = {image_max}"
    img_color = cv2.putText(img_color, text, (25, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
    if st_mean != 0 and st_std != 0:
        stats = f"Frame: {rec_count}_ Mu = {st_mean} || Std = {st_std} || MSE = {st_MSE}"
        img_color = cv2.putText(img_color, stats, (25, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

    # Add plot to bottom left corner of image
    plt_shape = overlay.shape
    img_color[(img_dim[0]-plt_shape[0]):img_dim[0], 0:plt_shape[1]] = overlay

    # Record Video if Heat is ongoing
    record_video(Desulf_Cam, therm_img, img_temp, img_color, frame_no)
    # vid_record_flag = flag

    # Show Processed Image at required size
    cam_resize = Desulf_Cam.get_resize()
    img_re = cv2.resize(img_color, (0, 0), fx=cam_resize, fy=cam_resize, interpolation=cv2.INTER_LINEAR)
    # img_re = cv2.resize(img_color, video_res, interpolation=cv2.INTER_LINEAR)
    Til.Show_Image("HamCam", f"{Desulf_Cam.get_camera_name()}: Image {frame_no} || fps = {Desulf_Cam.get_fps()}", img_re, 1)

    # Calculate FPS
    Desulf_Cam.calculate_fps(process_timer)
    # print("Working!!")

def therm_img_proc(camera, therm_img, pixel, img_color, brightness=1):
    """

    @return:
    """
    # Generate Thermal Image
    img_temp = Til.generate_temp_map(therm_img, pixel, camera.get_temp_scale())
    bits = Desulf_Cam.get_bit_depth()
    if brightness != 1:
        img = therm_img
        img[therm_img > int((2**bits-1)/brightness)] = (2**bits)-1  # 65535
        img = img * brightness
        # print(np.max(img))
        # ret, img = cv2.threshold(img, 65535, 65535, cv2.THRESH_TRUNC)
    else:
        img = therm_img
    img_color = Til.generate_temp_colormap(img, img_color, camera.get_color_scale())

    return img_temp, img_color

def record_video(camera, therm_img, img_temp, img_color, frame_no):
    """

    @return:
    """
    global vid_record_flag
    global rec_count
    global vid_date
    global start_time
    global finish_time

    dt = datetime.datetime.now()
    if camera.get_video_out() == "" or not vid_record_flag:
        camera.set_video_out(vid_name=VIDEOFILE, codec='mp4v', fps=FPS, video_res=video_res)

    # Define region of interest to acquire relative intensities
    vid_roi = therm_img[def_roi[0]:def_roi[1], def_roi[2]:def_roi[3]]

    # Calculate intensity percentage & add to roi_mean queue
    roi_mean.append((np.mean(vid_roi) / 255))
    # print(f"frame No: {frame_no}: roi_mean = {roi_mean}")

    # Check threshold to initialise and stop video recording
    if np.mean(roi_mean) > roi_thresh: # and rec_count % 2 == 0:
        if rec_count == 0:
            start_time = dt.strftime('%H-%M-%S')
            print(f"<--START RECORDING--> frame No: {frame_no}: roi_mean = {round(np.mean(roi_mean),2)}")
        # Write frame to video file
        vid_frame = cv2.resize(img_color, video_res, interpolation=cv2.INTER_LINEAR)
        rec_count = camera.capture_Video(vid_frame, rec_count, frame_no=18000)
        vid_record_flag = True
        #Save raw image to IMAGE_FOLDER
        if IMAGE_FOLDER != "" and rec_count % IMG_FREQ == 0:
            image_name = f"{UNIT_NAME}_{dt.strftime('%d-%m-%Y')}_{dt.strftime('%H-%M-%S-%f')}"
            Til.Save_tiff_Image(therm_img, IMAGE_FOLDER, image_name)

        # Save frame to desulf_queue to acquire best image of skim
        if frame_no % 5 == 0:
            queue_images(img_color, roi_mean[-1])

    elif rec_count > 250 and np.mean(roi_mean) < roi_thresh and vid_record_flag:
        print(f"<--STOP RECORDING--> frame No: {rec_count}: roi_mean = {round(np.mean(roi_mean), 2)}")
        # Stop video recording and rename video file
        camera.get_video_out().release()
        vid_date = dt.strftime('%Y-%m-%d')
        finish_time = dt.strftime('%H-%M-%S')
        name_vid_file(vid_date, start_time, finish_time)
        rec_count = 0
        vid_record_flag = False
        # Save best image at end of skim
        save_skim_image(vid_date, start_time, finish_time)

def stats_analysis(img_temp, temp_thresh=1000, bin_no=128):

    global vid_record_flag
    global rec_count
    global mu_target

    # Slice same ROI as video recording
    temp_roi = img_temp[def_roi[0]:def_roi[1], def_roi[2]:def_roi[3]]

    # Generate mask using Binary thresholding, threshold = temp_thresh
    thresh, mask = cv2.threshold(temp_roi, temp_thresh, 255, cv2.THRESH_BINARY)
    mask = np.uint8(mask)
    temp_roi = cv2.bitwise_and(temp_roi, temp_roi, mask=mask)
    T_max = round(float(np.amax(temp_roi)), 2)  # img_temp

    # Fit Normal distribution to temperature data and Calculate statistical moments
    try:
        stats_arr = temp_roi[temp_roi > 0].ravel()
        if len(stats_arr) != 0:
            mu, std = stats.norm.fit(stats_arr)

            temp_mean = round(float(mu), 2)
            temp_std = round(float(std), 2)
            # temp_mean = round(float(np.mean(stats_arr)), 2)
            # temp_std = round(float(np.std(stats_arr)), 2)

            # Plot measured temp data PDF
            # fun_time = time.time()
            plt.style.use("dark_background")
            fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
            # ax.set_title("Temperature Distribution")
            ax.set_xlabel("Temperature °C")
            plt.xlim(temp_thresh, 1450)
            ax.set_ylabel("Probability")
            ax.get_yaxis().set_visible(False)
            count, bins, _ = plt.hist(stats_arr, bins=bin_no, range=(thresh, np.max(stats_arr)),
                                        density=True, alpha=1, color='steelblue')
            # print(f"{rec_count}--> Plot Hist:{(time.time() - fun_time)}")

            # Calculate model PDF and mean square error (MSE)
            # fun_time = time.time()
            bin_size = bins[1] - bins[0]
            temp_data = bins[:-1] + bin_size / 2
            # pdf = stats.norm.pdf(temp_data, mu, std)
            # if (np.max(stats_arr)-(3 * std_target)) > mu_target-100:
            #     mu_target = temp_thresh+100
            # else:
            mu_target = (np.max(stats_arr)-(3 * std_target))

            pdf = stats.norm.pdf(temp_data, mu_target, std_target)
            sq_err = np.square(np.subtract(count, pdf))
            MSE = sq_err.mean() * 1000000
            TSE = round(float(sq_err.sum() * 1000000), 2)
            MSE = round(float(MSE), 2)

            # Plot the Modelled PDF
            plt.plot(temp_data, pdf, color='r', linewidth=2)
            # print(f"{rec_count}--> Plot Target:{(time.time() - fun_time)}")

            # Integrate to get area under the histogram
            # hist_area = np.trapz(y=count, x=temp_data)
            # gauss_area = np.trapz(y=pdf, x=temp_data)
            # print(f"Frame:{rec_count}-> Histogram Area = {hist_area.round(4)} "
            #       f"|| Gaussian Area = {gauss_area.round(4)} || Percentage = {(gauss_area/hist_area)*100}")

            # Extract plot as ndarray to overlay on image
            # fun_time = time.time()
            fig.canvas.draw()
            plt_overlay = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
            plt_overlay = plt_overlay.reshape(fig.canvas.get_width_height()[1], fig.canvas.get_width_height()[0], 3)
            plt_overlay = cv2.cvtColor(plt_overlay, cv2.COLOR_RGB2BGR)
            # cv2.imshow('Plot', plt_overlay)
            # cv2.waitKey(1)
            plt.close(fig)
            # print(f"{rec_count}--> Get Overlay:{(time.time() - fun_time)}")
        else:
            temp_mean, temp_std = st_mean, st_std
            MSE = st_MSE
            TSE = 0
            plt_overlay = overlay

        cost = 0
        # Add calculated frame stats to DataFrame
        stats_df.loc[len(stats_df)] = [rec_count, T_max, temp_mean, temp_std, MSE, TSE, cost]
        # print(f"{rec_count}--> T_max={T_max}, T_mean={temp_mean}, T_std={temp_std}, MSE={MSE}, TSE={TSE}, cost={cost}")

        return T_max, temp_mean, temp_std, MSE, plt_overlay

    except Exception as e:
        print(f"{rec_count}: Error during stats analysis _ {e}")
        traceback.print_exc()

def queue_images(img_color, roi_mean):
    """

    @param img_color:
    @param roi_mean:
    @return:
    """
    image_max = round(float(np.amax(roi_mean)), 2)
    frame = (img_color, image_max)
    if desulf_queue.full():
        desulf_queue.get_nowait()
    desulf_queue.put_nowait(frame)
    # Til.Show_Image("Queue", f"Length: {desulf_queue.qsize()}", img_color, 1)

def update_Alg_Settings_Dict(camera):
    """

    @param camera:
    @return:
    """
    try:
        Ex_time = camera.get_exposure_time()
    except AttributeError:
        Ex_time = 0.0

    ext = {"Unit_Name": UNIT_NAME,
           "Video_Size": VID_SIZE,
           "fps": FPS,
           "Video_Directory": DIRECTORY,
           "Image_Folder": IMAGE_FOLDER,
           "IMG_FREQ": IMG_FREQ,
           "Exposure_time": Ex_time
           }
    settings = camera.get_settings()
    # settings["Alg_Settings"].update(ext)
    settings["Alg_Settings"] = ext.copy()
    camera.create_settings_dict()


def save_skim_image(date, start, end):
    """

    @param date:
    @param start:
    @param end:
    @return:
    """
    percent_Skim = 100
    # img_max_vals = {}
    image = 0
    max_val = 0
    cnt = 0
    print(f"Queue Length: {desulf_queue.qsize()}")
    while not desulf_queue.empty(): ###########
        frame = desulf_queue.get()
        # img_max_vals[frame[1]] = frame[0]
        if frame[1] > max_val:
            max_val = frame[1]
            image = frame[0]
            # print(f"Max_val = {max_val}")
            # Til.Save_tiff_Image(image, DIRECTORY, f"{cnt}_{max_val}")
        cnt += 1
        # print(f"Queue Count: {desulf_queue.qsize()}")

    # Define image file Name and save as jpg
    # img_file = DIRECTORY + fr"\{UNIT_NAME}_{date}_{start}_{end}_{percent_Skim}_999.jpg"
    # cv2.imwrite(img_file, image)

    # Define image file Name and save image as tiff
    img_file = f"{UNIT_NAME}_{date}_{start}_{end}_{percent_Skim}_9999"
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    Til.Save_tiff_Image(image, DIRECTORY, img_file)

    # Save Stats_DataFrame as a CSV file of the same name
    stats_df.to_csv(fr"{DIRECTORY}\{img_file}.csv")
    # Re-initialize the Stats_DataFrame
    stats_df.drop(stats_df.index, inplace=True)

# MAIN
if __name__ == "__main__":

    # virtual_Cam.set_img_proc_func(virtual_Cam.get_img_proc_func())
    Desulf_Cam._func_img_proc = desulf_img_proc
    update_Alg_Settings_Dict(Desulf_Cam)
    print(Desulf_Cam.get_settings())

    try:
        Desulf_Cam.start()
        time.sleep(2)

        image_no = 0
        # image_qu = virtual_Cam.get_image_queue()
        while Desulf_Cam.is_alive():
            time.sleep(2)

            y = input("End Process (y/n): ")
            if y in ["y", "Y"]:
                print("stopping Process...")
                # Create settings.json
                # print(Desulf_Cam.get_settings())
                # if len(Desulf_Cam.get_settings().keys()) == 0:
                #     Desulf_Cam.save_settings_json("settings.json", Desulf_Cam.create_settings_dict())
                #     print("Created settings.json")
                # else:
                #     Desulf_Cam.save_settings_json("settings.json", Desulf_Cam.get_settings())
                #     print("Updated settings.json")
                Desulf_Cam.stop_process()
                Desulf_Cam.join(2)
                Desulf_Cam.terminate()
    except IndexError:
        logging.exception("No Cameras found!!")
    except KeyboardInterrupt:
        print(f"Stopping Process...")
        Desulf_Cam.stop_process()
        Desulf_Cam.join(2)
        Desulf_Cam.terminate()
        del Desulf_Cam

    cv2.destroyAllWindows()
    # VideoOut.release()
    # dt = datetime.datetime.now()
    # vid_date = dt.strftime('%d-%m-%Y')
    # start_time = dt.strftime('%H-%M-%S')
    # finish_time = dt.strftime('%H-%M-%S')
    # name_vid_file(vid_date, start_time, finish_time)

    print("Program Terminated!!!")
