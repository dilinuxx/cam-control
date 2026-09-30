import os
import multiprocessing as mp
import time

import ThermalImageLib as Til

class ImageProc(mp.Process):
    def __init__(self, img_qu):
        super(ImageProc, self).__init__()

        self._name = "Recording Process"
        self._folder_name = os.path.curdir
        self._image_queue = img_qu

        self._stop_event = mp.Event()

    def __str__(self):
        return (f"Recording Process {self.get_process_name()} started.\n"
                f"Recording at: {self.get_folder_name()}")

    def get_process_name(self):
        #
        return self._name

    def set_process_name(self, name):
        #
        self._name = name

    def get_folder_name(self):
        #
        return self._folder_name

    def set_folder_name(self, folder):
        #
        self._folder_name = folder

    def get_image_queue(self):
        #
        return self._image_queue

    def stop_process(self):
        """

        """
        self._stop_event.set()

    def run(self) -> None:
        print("Recording Data Starting!!!")
        time.sleep(2)
        while not self._stop_event.is_set():
            # Get Data from Image Queue
            if not self.get_image_queue().empty():
                frame = self.get_image_queue().get_nowait()

                frame_time = frame[0]
                therm_img = frame[1]
                # Save image to folder
                Til.Save_tiff_Image(therm_img, self.get_folder_name(), f"Image_{frame_time.replace(':', '_')}")
                # print("frame saved...")
            else:
                print("Waiting on image frames...")
                time.sleep(1)

        print(f"Recording Data Stopping!!!")
