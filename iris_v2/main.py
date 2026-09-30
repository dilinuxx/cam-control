import argparse
import logging

import ThermalImageLib as Til
import CameraManager.CameraManager_TH as Cam

# CONSTANTS
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", action="store_true", help="Print complete output")
parser.add_argument("-q", "--quite", action="store_true", help="Print concise output")

args = parser.parse_args()

# GLOBAL VARIABLES


# HELPER FUNCTIONS


# MAIN
if __name__ == "__main__":
    print(f"Colormaps: {Til.available_color_maps}")

    directory = "D:/PyrOptik/Python/CameraWebPlatform/Samples"

    virtual_Cam = Cam.CameraManager_Threaded()
    virtual_Cam.set_image_directory(directory)
    virtual_Cam.set_colormap('inferno')

    virtual_Cam.display_images()

    print("Success!!!")
