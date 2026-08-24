"""Sample for standard access image from DCIMG file.
Sample script for specifying file path and frame index.
And the received image is shown with OpenCV.
"""

__date__ = '2023-12-12'
__copyright__ = 'Copyright (C) 2024 Hamamatsu Photonics K.K.'

import os
# for getting file name form __file__

import cv2
# pip install opencv-python
# for disply image
# tested with (4.5.1.48) which used numpy (1.20.2)

from screeninfo import get_monitors
# pip install screeninfo
# for getting monitor information

from dcimgnp import *
# for control DCIMG function

def prompt_filepath():
    """Prompt and return file path.
    Prompt path of DCIMG file and return the input file path.

    Returns:
        str: file path
        bool: False if failure
    """
    prompt = '\nEnter DCIMG file path\n>'
    instr = ''
    try:
        instr = input(prompt)
    except ValueError:
        instr = None
    
    if instr is None:
        return False
    
    return instr

def prompt_frameindex(numberof_frame):
    """Prompt and return the target frame index.
    Prompt for the target index and return it if it is valid.
    The valid index is 0 to numberof_frame - 1.
    If the input value is invalid, repeat to prompt.

    Args:
        numberof_frame (int): number of frame in opened file
    
    Returns:
        int: target frame index
    """
    prompt = '\nEnter a value for target frame index'
    prompt += ' between 0 and ' + str(numberof_frame - 1)
    prompt += ' [default is 0]'
    prompt += '\n>'

    val = None
    while True:
        print()
        try:
            instr = input(prompt)
            val = int(instr)
        except ValueError:
            val = 0
            break

        if (val >= 0 and
            val < numberof_frame):
            break
    
    return val

def show_framedata(window_title, data):
    """Show frame data
    Open window of OpenCV with camera_title.
    Show numpy buffer as an image with OpenCV.

    Args:
        window_title (str): for OpenCV window title
        data (Numpy ndarray): numpy buffer stored image
    """
    # create OpenCV window
    cv2.namedWindow(window_title, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO | cv2.WINDOW_GUI_NORMAL)

    # resize display window
    data_width = data.shape[1]
    data_height = data.shape[0]

    window_pos_left = 156
    window_pos_top = 48

    screeninfos = get_monitors()

    max_width = screeninfos[0].width - (window_pos_left * 2)
    max_height = screeninfos[1].height - (window_pos_top * 2)

    if data_width > max_width:
        scale_X100 = int(100 * max_width / data_width)
    else:
        scale_X100 = 100
    
    if data_height > max_height:
        scale_Y100 = int(100 * max_height / data_height)
    else:
        scale_Y100 = 100
    
    if scale_X100 < scale_Y100:
        scale_100 = scale_X100
    else:
        scale_100 = scale_Y100
    
    disp_width = int(data_width * scale_100 * 0.01)
    disp_height = int(data_height * scale_100 * 0.01)

    cv2.resizeWindow(window_title, disp_width, disp_height)

    # move display window
    cv2.moveWindow(window_title, window_pos_left, window_pos_top)

    # show image
    cv2.imshow(window_title, data)
    cv2.waitKey(0)

if __name__ == '__main__':
    ownname = os.path.basename(__file__)
    print('Start {}'.format(ownname))

    # Dcimg instance
    dcimg = Dcimg()

    # prompt file path
    filepath = prompt_filepath()
    if filepath is not False:
        print()
        if not dcimg.open(filepath):
            print('-NG: Dcimg.open() failed with error()'.format(dcimg.lasterr().name))
        else:
            # show basic information of frame
            print(dcimg)
            frameindex = prompt_frameindex(dcimg.numberof_frame())
            print()

            window_title = 'frame{}'.format(frameindex)

            imgdata = dcimg.readframe(frameindex)
            if imgdata is not False:
                show_framedata(window_title, imgdata)

    print('End {}'.format(ownname))