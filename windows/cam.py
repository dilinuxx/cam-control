import sys
import os
import subprocess
import time

# Make the Hamamatsu Python SDK available
SDK_PATH = os.path.join(os.path.dirname(__file__), "dcamsdk4", "samples", "python")
sys.path.insert(0, SDK_PATH)

from dcam import Dcamapi, Dcam


def kill_dcamtray():
    """Kill DCAMTRAY because it can prevent DCAM API access."""
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", "DCAMTRAY.EXE"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        time.sleep(0.5)
    except Exception as e:
        print(f"Warning: could not kill DCAMTRAY: {e}")


def capture_image(filename="capture.tiff", device_index=0, timeout_ms=3000):
    print("=== Killing DCAMTRAY ===")
    kill_dcamtray()

    print("=== Initializing DCAM ===")
    if not Dcamapi.init():
        print("ERROR: Dcamapi.init() failed")
        print("DCAM error:", Dcamapi.lasterr())
        return False

    cam = None

    try:
        count = Dcamapi.get_devicecount()
        print("Device count:", count)

        if count <= device_index:
            print(f"ERROR: Device {device_index} does not exist")
            return False

        cam = Dcam(device_index)

        print("=== Opening camera ===")
        if not cam.dev_open(device_index):
            print("ERROR: dev_open() failed")
            print("DCAM error:", cam.lasterr())
            return False

        print("Camera opened:", cam.is_opened())

        # Import IDs after the camera is open.
        from dcamapi4 import DCAM_IDSTR

        print("Model:", cam.dev_getstring(DCAM_IDSTR.MODEL))
        print("Vendor:", cam.dev_getstring(DCAM_IDSTR.VENDOR))
        print("Camera ID:", cam.dev_getstring(DCAM_IDSTR.CAMERAID))

        print("=== Allocating buffer ===")
        if not cam.buf_alloc(1):
            print("ERROR: buf_alloc() failed")
            print("DCAM error:", cam.lasterr())
            return False

        try:
            print("=== Taking snapshot ===")

            if not cam.cap_snapshot():
                print("ERROR: cap_snapshot() failed")
                print("DCAM error:", cam.lasterr())
                return False

            print("Waiting for frame...")

            if not cam.wait_capevent_frameready(timeout_ms):
                print("ERROR: timeout/wait failed")
                print("DCAM error:", cam.lasterr())
                return False

            print("Frame ready!")

            data = cam.buf_getlastframedata()

            if data is False:
                print("ERROR: could not retrieve frame")
                print("DCAM error:", cam.lasterr())
                return False

            print("Image type:", type(data))
            print("Image dtype:", data.dtype)
            print("Image shape:", data.shape)
            print("Image min:", data.min())
            print("Image max:", data.max())

            # Save using OpenCV if available.
            try:
                import cv2

                if not cv2.imwrite(filename, data):
                    print("ERROR: OpenCV could not write image")
                    return False

                print("Saved:", os.path.abspath(filename))

            except ImportError:
                print("OpenCV is not installed.")
                print("Install it with:")
                print("pip install opencv-python")
                return False

            return True

        finally:
            print("=== Releasing buffer ===")
            cam.buf_release()

    finally:
        if cam is not None and cam.is_opened():
            print("=== Closing camera ===")
            cam.dev_close()

        print("=== Uninitializing DCAM ===")
        Dcamapi.uninit()


if __name__ == "__main__":
    success = capture_image("capture.tiff")

    print()
    if success:
        print("SUCCESS: image captured.")
    else:
        print("FAILED: image was not captured.")
