"""
############
DESCRIPTION:
############

#####
TO DO:
#####
1- Generate image gradient and plot its magnitude and orientation, can be useful in segmenting thermal zones
2-
#####
BUGS:
#####
-> Cython methods in Thermal_cy can't be found by the python linter which shows as an unresolved reference error, but
    the functions run without issue
"""

import cv2
import numpy as np
import tifffile
from skimage.feature import peak_local_max
from skimage.segmentation import watershed
from scipy import ndimage

from matplotlib import pyplot as plt, colors, colorbar, use

from ThermalImageLib.Thermal_cy.thermal_transform import img_thermal, img_colormap

use("Agg")

# CONSTANTS
available_color_maps = ['afmhot', 'cubehelix', 'inferno', 'magma']

# DISPLAY FUNCTIONS
def Show_Image(winName: str, winTitle: str, image, wait: int):
    """
    Display image in a window using Open-CV.
    @param winName: Name handle for image window
    @param winTitle: Title to be displayed on image window
    @param image: Matrix defining an image, numpy array
    @param wait: Define delay length in ms before closing window
    """
    cv2.imshow(winName, image)
    cv2.setWindowTitle(winName, winTitle)
    cv2.waitKey(wait)    

def Overlay_Text(image, text, origin=(50, 50), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1,
                 color=(0, 255, 0), thickness=2):
    """
    Display text information inside an existing image
    @param image: Numpy array of image
    @param text: Information to be displayed on image
    @param origin: Define location of bottom left corner of text to be displayed
    @param fontFace: OpenCV font type to be used
    @param fontScale: Font size
    @param color: Font color
    @param thickness: Font thickness
    @return: processed image with text overlayed
    """
    cv2.putText(image, f'{text}', origin, fontFace, fontScale, color, thickness)
    return image

# Image Processing functions
def Sharpen_Image(image):
    """
    Sharpen image using OpenCV filter2D & 3x3 kernel
    @param image: Numpy array of image to be sharpened
    @return: sharpened image
    """
    kernel3 = np.array([[0, -1, 0],
                        [-1, 5, -1],
                        [0, -1, 0]])
    return cv2.filter2D(src=image, ddepth=-1, kernel=kernel3)

# Colormap and Colorbar Functions
def Create_ColorMap(name='afmhot', no_Bits=16, scale=2):
    """
    Create Matplotlib colormap object with 2^n colors to apply to images
    @param name: Matplotlib colormap name, Recommended in available_color_maps list
    @param no_Bits: Define the colormap bit depth in bits
    @param scale: Assign number of colormap colors to be displayed
    @return: Matplotlib colormap object
    """
    no_color = 2**no_Bits
    color_map = plt.cm.get_cmap(name, lut=int(no_color/scale))

    return color_map

def Apply_Colormap(color_map, image):
    """
    Apply Matplotlib colormap to image
    @param color_map: Matplotlib colormap name, Recommended in available_color_maps list
    @param image: Matrix defining an image, numpy array
    @return: processed image with defined colormap
    """
    image = color_map(image)
    image = np.uint8(image * 255)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    return image

def Draw_ColorBar(color_map, colorbar_min, colorbar_max, filename="../Horizontal_Colorbar.png", orient="horizontal"):
    """
    Generate a Colorbar as a .PNG image with a specified colormap, temperature range and orientation
    @param color_map: Matplotlib colormap name, Recommended in available_color_maps list
    @param colorbar_min: Colorbar minimum temperature
    @param colorbar_max: Colorbar maximum temperature
    @param filename: Save colorbar, format: PNG
    @param orient: Define Colorbar orientation, Default: horizontal
    """
    plt.ioff()
    with plt.rc_context({'xtick.color': 'white', 'ytick.color': 'white'}):
        norm = colors.Normalize(vmin=colorbar_min, vmax=colorbar_max)
        if orient == "horizontal":
            fig = plt.figure(figsize=(8, 1))                # figure size=(width, height)
            ax1 = fig.add_axes([0.05, 0.3, 0.9, 0.3])       # fig.add_axes(rect=[left, bottom, width height])

            colorbar.ColorbarBase(ax1, cmap=color_map, norm=norm, orientation="horizontal")
        elif orient == "vertical":
            fig = plt.figure(figsize=(1.5, 8))              # figure size=(width, height)
            ax1 = fig.add_axes([0.3, 0.05, 0.3, 0.9])       # fig.add_axes(rect=[left, bottom, width height])

            colorbar.ColorbarBase(ax1, cmap=color_map, norm=norm, orientation="vertical")

        else:
            raise Exception("Colorbar orientation can only be 'horizontal' or 'vertical'")

        plt.savefig(filename, format="png", dpi=100, transparent=True)
        plt.close(fig)
    print(f'Colorbar image created at {filename}')

# Thermal Imaging Functions
def CurveFitting_Thermal_Image(Thermal_Cal: tuple, image):
    """
    Generate Thermal Image using 3-point curve fitting calibration,
    if Image is an integer return the equivalent temperature
    @param Thermal_Cal: List of 3-point calibration constants
    @param image: Greyscale image
    @return: processed coloured Thermal image, Maximum temperature in image, Maximum temperature index,
            Minimum temperature in image, Minimum temperature index
    """
    a = Thermal_Cal[0]
    b = Thermal_Cal[1]
    c = Thermal_Cal[2]

    therm_img = (a * (image**b)) + c

    if type(image) != int:
        image_max, image_min = round(np.amax(therm_img), 1), round(np.amin(therm_img), 1)
        max_index = np.unravel_index(np.argmax(therm_img), therm_img.shape)
        min_index = np.unravel_index(np.argmin(therm_img), therm_img.shape)

        # therm_img = np.array(image)

        # therm_img = Apply_Colormap(color_map, therm_img)

        return therm_img, image_max, max_index, image_min, min_index
    else:
        return therm_img

def Ambient_Temp_Correction():

    pass

# Fast Thermal Image Transform - Cython
def generate_temp_scale(bits, thermal_cal, trans_co=1):
    """

    @param bits:
    @param thermal_cal:
    @param trans_co:
    @return:
    """
    temp_scale = np.arange(0, (2**bits), 1)
    temp_scale = temp_scale / trans_co
    temp_scale = (thermal_cal[0] * (temp_scale ** thermal_cal[1])) + thermal_cal[2]

    return temp_scale.astype(np.single)

def generate_color_scale(colormap, bits):
    """

    @param colormap:
    @param bits:
    @return:
    """
    cmap = plt.cm.get_cmap(colormap, lut=2**bits)
    N = 2 ** bits
    color_scale = np.arange(0, N, 1)
    color_scale = color_scale.reshape(256, 256)/max(color_scale)
    color_scale = cmap(color_scale)
    color_scale = np.uint8(color_scale*255)
    color_scale = cv2.cvtColor(color_scale, cv2.COLOR_RGB2BGR)
    color_scale = color_scale.astype(int)
    color_scale = color_scale.reshape(2**bits, 3)
    color_scale = np.uint8(color_scale)

    return color_scale

def generate_color_scale_twoSlope(colormap, bits, temp_scale, smin=0.5, scenter=0.7):
    """

    @param colormap:
    @param bits:
    @param temp_scale:
    @param smin:
    @param smax:
    @return:
    """
    temp_min = temp_scale[0]
    temp_max = temp_scale[-1]
    ax = plt.subplots(1, 1)[1]
    # reshape temp_scale to a square
    square_size = int(2**(bits/2))
    cs = temp_scale.reshape(square_size, square_size)/temp_max

    # define normalization
    div_norm = colors.TwoSlopeNorm(vmin=smin*temp_max, vcenter=scenter*temp_max, vmax=1*temp_max)
    cs_img = ax.pcolormesh(np.multiply(cs, temp_max), norm=div_norm, cmap=colormap, shading='auto')
    a = cs_img.get_array()
    a = a.reshape(cs.shape)

    rgbas = cs_img.to_rgba(a)
    therm_color_scale = np.uint8(rgbas*255)
    therm_color_scale = cv2.cvtColor(therm_color_scale, cv2.COLOR_RGB2BGR)
    therm_color_scale = therm_color_scale.astype(int)
    therm_color_scale = therm_color_scale.reshape(2**bits, 3)
    therm_color_scale = np.uint8(therm_color_scale)
    
    return therm_color_scale

def generate_temp_map(img_raw, t_matrix, temp_scale):
    """
    Use cython img_thermal to generate temperature image based on temp_scale
    @param img_raw:
    @param t_matrix:
    @param temp_scale:
    @return:
    """
    return np.asarray(img_thermal(img_raw, t_matrix, temp_scale))

def generate_temp_colormap(img_raw, img_therm, color_scale):
    """
    Use cython img_colormap to generate color image based on color_scale
    @param img_raw:
    @param img_therm:
    @param color_scale:
    @return:
    """
    return np.asarray(img_colormap(img_raw, img_therm, color_scale))

# Image File manipulation functions
def Save_tiff_Image(image,  directory_path="", filename=""):
    """

    @param image:
    @param directory_path:
    @param filename:
    @return:
    """
    if directory_path == "":
        directory_path = "../"
    if filename == "":
        filename = "TestImage"
    with tifffile.TiffWriter(f"{directory_path}/{filename}.tif", append=False) as tiff:
        tiff.write(image)

    #return f"{directory_path}/{filename}.tif"


def apply_watershed(image, clip_limit=2.0):
    """
    Display text information inside an existing image
    @param image: Numpy array of image
    @param clip_limit: histogram clipping limit (default = 2.0)
    @return: processed image with contours determined from watershed algorithm overlayed, areas of contours
    """

    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
    image = clahe.apply(image)
    img_col = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    image = cv2.normalize(image, None, 0, 255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    thresh = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    # Compute Euclidean distance from every binary pixel
    # to the nearest zero pixel then find peaks
    distance_map = ndimage.distance_transform_edt(thresh)
    local_max = peak_local_max(distance_map, indices=False, min_distance=20, labels=thresh)

    # Perform connected component analysis then apply Watershed
    markers = ndimage.label(local_max, structure=np.ones((3, 3)))[0]
    labels = watershed(-distance_map, markers, mask=thresh)

    # Iterate through unique labels
    areas = []
    for label in np.unique(labels):
        if label == 0:
            continue
        # Create a mask
        mask = np.zeros(img.shape, dtype="uint8")
        mask[labels == label] = 255

        # Find contours and determine contour area
        cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]
        c = max(cnts, key=cv2.contourArea)
        area = cv2.contourArea(c)
        areas.append(area)
        # Nick's code used 400 as threshold
        if area > 400:
            cv2.drawContours(img_col, [c], -1, (0, 255, 0), 1)

    return img_col, areas

# MAIN
if __name__ == "__main__":

    from time import time_ns

    THERMAL_CALIBRATION = (171.4, 0.1339, 196.2)  # A, B, C => Strand-End Hamamatsu

    # Test intensity to temperature conversion
    min_temp = round(CurveFitting_Thermal_Image(THERMAL_CALIBRATION, 0), 2)
    max_temp = round(CurveFitting_Thermal_Image(THERMAL_CALIBRATION, 2**16), 2)
    print(f'Minimum Temp: {min_temp}; Maximum Temp: {max_temp}')

    # Test Show Raw Image
    # img = cv2.imread("../Samples/Test_img_11.tif", cv2.IMREAD_ANYDEPTH)
    img = cv2.imread("D:\\PyrOptik\\Python\\IRIS\\Samples\\Image1_01.tif", cv2.IMREAD_ANYDEPTH)
    # img = cv2.imread("../Samples/Tuyere_img_02.tif", cv2.IMREAD_ANYDEPTH)

    # img = img[2048-1920:, 2048-1080:]
    # img = cv2.resize(img, (0, 0), fx=0.5, fy=0.5, interpolation=cv2.INTER_LINEAR)
    # Show_Image("RawImage", "Test Raw Image", img, 0)
    print(f"Image dimensions: {img.shape}")

    # Save image in Tiff file
    # path = Save_tiff_Image(img)

    # Test Thermal image generation

    COLORMAP = Create_ColorMap('cubehelix', scale=1)
    Show_Image("ThermalImage", "Test Thermal Image", img, 1)

    start_time = time_ns()
    therm, img_max, max_idx, img_min, min_idx = CurveFitting_Thermal_Image(THERMAL_CALIBRATION, img)
    t_therm = time_ns()-start_time

    start_time = time_ns()
    thermal = Apply_Colormap(color_map=COLORMAP, image=therm)
    t_cmap = time_ns()-start_time

    # thermal = thermal.reshape(2048, 2048)

    start_time = time_ns()
    Show_Image("ThermalImage", "Test Thermal Image", thermal, 1)
    t_cv_show = time_ns()-start_time

    print(f"Max Temp: {img_max}, Max Loc: {max_idx} || "
          f"Min Temp: {img_min}, Min Loc: {min_idx}")

    print(f"Thermal Image shape: {thermal.shape}")
    print(f"Total time: {(t_therm + t_cmap + t_cv_show)/1000000000} || "
          f"Thermal Transform time: {t_therm/1000000000} || "
          f"Colormap time: {t_cmap/1000000000} || "
          f"Cv2 render time: {t_cv_show/1000000000}")

    # Test Colorbar generation
    # colormap = Create_ColorMap('magma', scale=1)
    # Draw_ColorBar(color_map=colormap, colorbar_min=0, colorbar_max=2500, orient="horizontal")

    # Test Colormap to numpy array
    # colormap = Create_ColorMap('cubehelix', scale=1)
    # cm_array = np.arange(0, 2**16)
    # cm_array = cm_array.reshape(256, 256)
    # coloured_array = colormap(cm_array)
    # coloured_array = np.uint8(coloured_array * 255)
    # coloured_array = cv2.cvtColor(coloured_array, cv2.COLOR_RGB2BGR)
    # Show_Image("Colormap", "Test colormap", coloured_array, 1)
    #
    # therm_array = CurveFitting_Thermal_Image(THERMAL_CALIBRATION, cm_array)[0]
    # coloured_array = colormap(therm_array)
    # coloured_array = np.uint8(coloured_array * 255)
    # coloured_array = cv2.cvtColor(coloured_array, cv2.COLOR_RGB2BGR)
    # Show_Image("Thermal map", "Thermal colormap", coloured_array, 0)

    # Cython Apply color map
    t_scale = generate_temp_scale(16, THERMAL_CALIBRATION)
    c_scale = generate_color_scale("cubehelix", 16)
    c_scale = np.uint8(c_scale)
    # img = np.uint16(img)

    pixel = np.zeros(img.shape, dtype=np.single)

    t_cmap = time_ns()
    img_temp = generate_temp_map(img, pixel, t_scale)
    t_cmap = time_ns() - t_cmap

    img_out = np.zeros((img.shape[0], img.shape[1], 3), dtype=int)
    img_out = np.uint8(img_out)

    t_cv_show = time_ns()
    img_out = generate_temp_colormap(img, img_out, c_scale)
    t_cv_show = time_ns() - t_cv_show

    # img_out = np.asarray(img_out)
    # cv2.imshow("Cython Cmap", img_out)
    # cv2.waitKey(0)
    img_temp = np.asarray(img_temp)
    t_max = img_temp.max()
    t_min = img_temp.min()
    max_loc = np.unravel_index(np.argmax(img_temp), img_temp.shape)
    min_loc = np.unravel_index(np.argmin(img_temp), img_temp.shape)

    print(f"Max Temp: {round(t_max, 1)}, Max Loc: {max_loc} || "
          f"Min Temp: {round(t_min, 1)}, Min Loc: {min_loc}")

    print(f"New Thermal image time: {t_cmap/1000000000}s || "
          f"New Colormap time: {t_cv_show/1000000000}s")

    print("Success!!!")
