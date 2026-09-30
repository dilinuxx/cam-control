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

        self._colormap = 'afmhot'
        self._bit_depth = 16
        self._colormap_scale = 2
        self._thermal_cal = (171.4, 0.1339, 196.2)      # A, B, C
        self._resize = 0.5
        self._fps = 0
        self._image_queue = queue.Queue(maxsize=2)
        self._stop_event = threading.Event()
        print(f"Threaded Camera manager name: {self._camera}\n"
              f"Directory: {self._image_directory}\n"
              f"Colormap : {self._colormap}; Color Scale = {self._colormap_scale}\n"
              f"Thermal Calibration: {self._thermal_cal}; Image Size = {self._resize}")

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

    def get_bit_depth(self):
        #
        return self._bit_depth

    def get_colormap_scale(self):
        #
        return self._colormap_scale

    def set_colormap_scale(self, scale):
        #
        self._colormap_scale = scale

    def get_thermal_Cal(self):
        #
        return self._thermal_cal

    def set_thermal_Cal(self, thermal_cal):
        #
        self._thermal_cal = thermal_cal

    def get_resize(self):
        #
        return self._resize

    def set_resize(self, resize):
        #
        self._resize = resize

    def get_fps(self):
        #
        return self._fps

    def calculate_fps(self, start):
        """

        @param start:
        @return:
        """
        self._fps = round(1000000000/ (time.time_ns() - start),2)

    def get_image_queue(self):
        """

        """
        return self._image_queue

    def stop_thread(self):
        """

        """
        self._stop_event.set()

    def create_image_list(self):
        """

        @return:
        """
        sampleList = os.listdir(self._image_directory)
        return sampleList

    def display_images(self):
        print("Start Image Display...")
        # Create Thermal image color map
        COLORMAP = Til.Create_ColorMap(self._colormap, no_Bits=self._bit_depth, scale=self._colormap_scale)

        # Generate Image list from directory
        image_id = 0
        image_list = self.create_image_list()
        while image_id < len(image_list) and not self._stop_event.is_set():
            process_timer = time.time_ns()
            # print(f"Image ID: {image_list[image_id]} || Queue Length: {self._image_queue.qsize()}")
            # Read Raw image
            image = cv2.imread(f"{self._image_directory}/{image_list[image_id]}", cv2.IMREAD_ANYDEPTH)

            # Add image processing algorithm
            # ...

            # Create temperature image with colormap
            therm_img, image_max, max_index, image_min, min_index = Til.CurveFitting_Thermal_Image(self._thermal_cal,
                                                                                                   image, COLORMAP)
            therm_img = Til.Apply_Colormap(COLORMAP, therm_img)
            # Sharpen teperature image
            therm_img = Til.Sharpen_Image(therm_img)
            # Resize & Show image
            therm_img = cv2.resize(therm_img, (0, 0), fx=self._resize, fy=self._resize, interpolation=cv2.INTER_LINEAR)
            Til.Show_Image("ThermImage", "Thermal Image", therm_img, 1)

            # Calculate FPS
            self.calculate_fps(process_timer)
            print(f"FPS = {self._fps}")

            image_id += 1
        print(f"Total image processed = {image_id}")

    def run(self) -> None:
        print(f"{self._camera} Manager Thread Starting...")
        # Create Thermal image color map
        COLORMAP = Til.Create_ColorMap(self._colormap, no_Bits=self._bit_depth, scale=self._colormap_scale)

        # Generate Image list from directory
        image_list = self.create_image_list()

        # Iterate through image list
        image_id = 0
        while image_id < len(image_list) and not self._stop_event.is_set():
            process_timer = time.time_ns()
            # print(f"Image ID: {image_list[image_id]} || Queue Length: {self._image_queue.qsize()}")
            # Read Raw image
            image = cv2.imread(f"{self._image_directory}/{image_list[image_id]}", cv2.IMREAD_ANYDEPTH)
            # image = cv2.resize(image, (0,0), fx=self._resize, fy=self._resize, interpolation=cv2.INTER_LINEAR)

            # Add image processing algorithm
            # ...

            # Create temperature image with colormap
            therm_img, image_max, max_index, image_min, min_index = Til.CurveFitting_Thermal_Image(self._thermal_cal, image, COLORMAP)
            therm_img = Til.Apply_Colormap(COLORMAP, therm_img)
            # Sharpen teperature image
            therm_img = Til.Sharpen_Image(therm_img)
            # Resize & Show image
            therm_img = cv2.resize(therm_img, (0,0), fx=self._resize, fy=self._resize, interpolation=cv2.INTER_LINEAR)
            Til.Show_Image("ThermImage", "Thermal Image", therm_img, 1)

            # Add Processed image to Queue
            # if self._image_queue.full():
            #     print("Image Queue full!! Waiting 1s...")
            #     time.sleep(0.2)
            #     self._image_queue.put_nowait(image)
            # else:
            #     self._image_queue.put_nowait(image)
            #     print(f"Image {image_id} Added to Queue")
            #     time.sleep(0.2)

            # Calculate FPS
            self.calculate_fps(process_timer)
            print(f"FPS = {self._fps}")

            image_id += 1
        print(f"Total image processed = {image_id}")

# MAIN
if __name__ == "__main__":
    directory = "D:/PyrOptik/Python/CameraWebPlatform/Samples"

    virtual_Cam = CameraManager_Threaded()
    virtual_Cam.set_image_directory(directory)
    virtual_Cam.set_colormap('afmhot')

    # virtual_Cam.display_images()

    # print(virtual_Cam.get_camera_name())
    virtual_Cam.start()
    time.sleep(0.5)

    image_no = 0
    image_qu = virtual_Cam.get_image_queue()
    while virtual_Cam.is_alive():
        # time.sleep(0.1)
        # if image_qu.empty():
        #     # print(f"Image Queue is Empty!!!")
        #     pass
        # else:
        #     image_qu.get_nowait()
        #     # print(f"Image {image_no} retrived from Queue")
        #     image_no += 1

        y = input("End thread (Y/n): ")
        if y == "Y":
            print("stopping Thread...")
            virtual_Cam.stop_thread()
            virtual_Cam.join()
            if not virtual_Cam.is_alive():
                print("Thread Terminated!!")

    print("Program Terminated!!!")
