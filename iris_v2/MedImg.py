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
import matplotlib.colors as colors
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
import cv2

IMG_FOLDER = r"D:\PyrOptik\MRC_IAA_2023-11-06_11-57-21"
# IMG_FOLDER = r"D:\PyrOptik\MRC_IAA_2023-12-04_13-02-01"

CMAP = "gray"       # LINK: https://matplotlib.org/stable/users/explain/colors/colormaps.html
WAIT = 1

# Define Thermal Calibration
Thermal_Cal = (215.4, 0.154, 261.8)

#
int_val = 30
prev_img = 0
diff_img = 0

# Start and end frames
start = "40"
end = "100"


def ListSort_Func(data):
    key = data.split('.')[0]
    key = int(key)
    return key


def CV_img_plt(image, index, win_title):
    fig, ax = plt.subplots(layout="constrained")  # figsize=(10, 4)
    fig.set_facecolor('white')
    plt.imshow(image, cmap=CMAP)
    plt.title(f"Image:{sample_list[index].split('.')[0]} - "
              f"Max={np.max(image)} - Min={np.min(image)}")
    plt.colorbar(orientation='vertical')

    fig.canvas.draw()
    cv_img = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
    cv_img = cv_img.reshape(fig.canvas.get_width_height()[1], fig.canvas.get_width_height()[0], 3)
    cv_img = cv2.cvtColor(cv_img, cv2.COLOR_RGB2BGR)
    cv2.imshow(f"{win_title}_Image Size={image.shape}", cv_img)
    # cv2.waitKey(WAIT)

    plt.close(fig)


if __name__ == "__main__":
    # Generate Test Image List
    sample_list = [x for x in os.listdir(IMG_FOLDER) if x.endswith('.tif')]
    sample_list = [x for x in sample_list if not x.__contains__('(')]
    sample_list.sort(key=ListSort_Func)
    print(f"Test Image No. = {len(sample_list)}")

    if start != "" and end != "":
        start_idx = sample_list.index(f"{start}.tif")
        end_idx = sample_list.index(f"{end}.tif")
        sample_list = sample_list[start_idx:end_idx+1]
        print(f"Sample List Slice Image No. = {len(sample_list)}")

    for idx, x in enumerate(sample_list):
        img = cv2.imread(fr"{IMG_FOLDER}\\{sample_list[idx]}", cv2.IMREAD_ANYDEPTH)

        # Normalize image
        img_max = np.max(img)
        img_min = np.min(img)
        norm_img = (img - img_min)/(img_max - img_min)

        # Difference image
        if idx == 0 or idx % int_val == 0:
            diff_img = np.zeros(norm_img.shape)
        else:
            diff_img += norm_img - prev_img

        prev_img = norm_img

        # CV_img_plt(img, idx, "Raw Sample Images")
        CV_img_plt(norm_img, idx, "Normalized Sample Images")
        # CV_img_plt(diff_img, idx, "Gradient Sample Images")
        cv2.waitKey(WAIT)

    print("Sample List Complete.")
