import cv2
import numpy as np

from matplotlib import pyplot as plt, colors, colorbar, use

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
def CurveFitting_Thermal_Image(Thermal_Cal: tuple, image, color_map=Create_ColorMap()):
    """
    Generate Thermal Image using 3-point curve fitting calibration,
    if Image is an integer return the equivalent temperature
    @param Thermal_Cal: List of 3-point calibration constants
    @param image: Greyscale image
    @param color_map: Matplotlib colormap name, Recommended in available_color_maps list
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

        therm_img = np.array(image)

        therm_img = Apply_Colormap(color_map, therm_img)

        return therm_img, image_max, max_index, image_min, min_index
    else:
        return therm_img

def Ambient_Temp_Correction():
    pass

# MAIN
if __name__ == "__main__":
    THERMAL_CALIBRATION = (171.4, 0.1339, 196.2)  # A, B, C => Strand-End Hamamatsu

    # Test intensity to temperature conversion
    min_temp = round(CurveFitting_Thermal_Image(THERMAL_CALIBRATION, 0), 2)
    max_temp = round(CurveFitting_Thermal_Image(THERMAL_CALIBRATION, 2**16), 2)
    print(f'Minimum Temp: {min_temp}; Maximum Temp: {max_temp}')

    # Test Show Raw Image
    img = cv2.imread("../Samples/Image1_01.tif", cv2.IMREAD_ANYDEPTH)
    img = cv2.resize(img, (0, 0), fx=0.4, fy=0.4, interpolation=cv2.INTER_LINEAR)
    Show_Image("RawImage", "Test Raw Image", img, 0)

    # Test Thermal image generation
    therm, img_max, max_idx, img_min, min_idx = CurveFitting_Thermal_Image(THERMAL_CALIBRATION, img, color_map=Create_ColorMap('magma'))
    Show_Image("ThermalImage", "Test Thermal Image", therm, 0)

    # Test Colorbar generation
    # colormap = Create_ColorMap('magma', scale=1)
    # Draw_ColorBar(color_map=colormap, colorbar_min=0, colorbar_max=2500, orient="horizontal")

    print("Success!!!")
