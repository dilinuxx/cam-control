import os
import queue
import time
import threading

import cv2

import ThermalImageLib as Til

# CONSTANTS


# CLASSES
class CameraManager_Threaded(threading.Thread):

    def __init__(self):
        super().__init__()
        self._camera = 'VirtualCam'
        self._image_directory = ''

        self._colormap = self.set_colormap('')
        self._bit_depth = 16
        self._colormap_scale = 2
        self._image_queue = queue.Queue(maxsize=0)
        self._stop_event = threading.Event()

    def set_camera_name(self, name):
        #
        self._camera = name

    def get_camera_name(self):
        #
        return self._camera

    def get_image_directory(self):
        #
        return self._image_directory

    def set_image_directory(self, directory_path:str):
        #
        self._image_directory = directory_path

    def get_colormap(self):
        #
        return self._colormap

    def set_colormap(self, colormap:str):
        #
        self._colormap = colormap

    def get_image_queue(self):
        """

        """
        return self._image_queue

    def stop_thread(self):
        """

        """
        self._stop_event.set()

    def save_raw_image(self):
        pass

    def create_image_list(self):
        """

        @return:
        """
        sampleList = os.listdir(self._image_directory)
        return sampleList

    def run(self) -> None:
        print("Camera Manager Thread Starting...")
        # Create Thermal image color map
        COLORMAP = Til.Create_ColorMap(self._colormap, no_Bits=self._bit_depth, scale=self._colormap_scale)

        # Generate Image list from directory
        image_id = 0
        image_list = self.create_image_list()
        while image_id < len(image_list) and not self._stop_event.is_set():
            # print(f"Image ID: {image_list[image_id]} || Queue Length: {self._image_queue.qsize()}")
            # Read Raw image
            image = cv2.imread(f"{self._image_directory}/{image_list[image_id]}", cv2.IMREAD_ANYDEPTH)
            # Add Processed image to Queue
            if self._image_queue.full():
                print("Image Queue full!! Waiting 1s...")
                time.sleep(0.5)
                self._image_queue.put_nowait(image)
            else:
                self._image_queue.put_nowait(image)
                print(f"Image {image_id} Added to Queue")
                time.sleep(0.5)

            image_id += 1
        pass

# MAIN
if __name__ == "__main__":
    directory = "D:/PyrOptik/Python/CameraWebPlatform/Samples"

    virtual_Cam = CameraManager_Threaded()
    virtual_Cam.set_image_directory(directory)
    virtual_Cam.set_colormap('afmhot')

    print(virtual_Cam.get_camera_name())
    virtual_Cam.start()
    time.sleep(0.5)

    image_no = 0
    image_qu = virtual_Cam.get_image_queue()
    while virtual_Cam.is_alive():
        time.sleep(0.1)
        if image_qu.empty():
            # print(f"Image Queue is Empty!!!")
            pass
        else:
            image_qu.get_nowait()
            # print(f"Image {image_no} retrived from Queue")
            image_no += 1

        y = input("End thread (Y/n): ")
        if y == "Y":
            print("stopping Thread...")
            virtual_Cam.stop_thread()
            virtual_Cam.join()
            if not virtual_Cam.is_alive():
                print("Thread Terminated!!")

    print("Program Terminated!!!")
