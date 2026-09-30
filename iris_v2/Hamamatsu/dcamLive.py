import cv2
from dcam import *

def dcam_show_device_list():
    """ Show HAMAMATSU Device List """ 
    if Dcamapi.init() is not False:
        n = Dcamapi.get_devicecount()
        for i in range(0,n):
            dcam = Dcam(i)
            output = '###{}: '.format(i)

            model = dcam.dev_getstring(DCAM_IDSTR.MODEL)
            if model is False:
                output = output + 'No DCAM_IDSTR.MODEL'
            else:
                output = output + 'MODEL = {}'.format(model)

            cameraID = dcam.dev_getstring(DCAM_IDSTR.CAMERAID)
            if cameraID is False:
                output = output + ', No DCAM_IDSTR.CAMERAID'
            else:
                output = output + ', CAMERAID = {}'.format(cameraID)

            print(output)
    else:
        print('-NG: Dcamapi.init() fails with error {}'.format(Dcamapi.lasterr()))

    Dcamapi.uninit()


def dcam_show_framedata(data, windowtitle, iShown):
    """
    Show numpy buffer as an image

    Arg1:   NumPy array
    Arg2:   Window name
    Arg3:   Last window status.
        0   open as a new window
        <0  already closed
        >0  already openend
    """
    if iShown > 0 and cv2.getWindowProperty(windowtitle, 0) < 0:
        return -1 # Window has been closed
    if iShown < 0:
        return -1 # Window is already closed
    
    if data.dtype == np.uint16:
        imax = np.amax(data)
        if imax > 0:
            imul = int(65535 / imax)
            # print('Multiple %s' % imul)
            data = data * imul

        cv2.imshow(windowtitle, data)
        cv2.waitKey(0)
        return 1
    else:
        print ('')
        return -1


def dcam_generate_frames(data):
    """
    """
    if data.dtype == np.unit16:
        imax = np.amax(data)
        if imax > 0:
            imul = int(65535 / imax)
            #
            data = data * imul

    ret, buffer = cv2.imencode('.jpg', data)
    frame = buffer.tobytes()

    yield(b'--frame\r\n' b'Content-Type: image/png\r\n\r\n' + frame + b'\r\n')


def dcam_thread_live(dcam):
    """
    Show live image

    Arg1: Dcam instance
    """
    if dcam.cap_start() is not False:
        timeout_milisec = 100
        iWindowStatus = 0
        while iWindowStatus >= 0:
            if dcam.wait_capevent_frameready(timeout_milisec) is not False:
                data = dcam.buf_getlastframedata()
                iWindowStatus = dcam_show_framedata(data, 'test', iWindowStatus)
                #dcam_generate_frames(data)
            else:
                dcamerr = dcam.lasterr()
                if dcamerr.is_timeout():
                    print('===: timeout')
                else:
                    print('-NG: Dcam.wait_event() fails with error {}'.format(dcamerr))
                    break
            
            ret, buffer = cv2.imencode('.jpg', data)
            frame = buffer.tobytes()

            yield(b'--frame\r\n' b'Content-Type: image/png\r\n\r\n' + frame + b'\r\n')
            # if 'q' or 'Q' was pressed with the live window, close it
            #key = cv2.waitKey(1)
            #if key == ord('q') or key == ord('Q'):
            #    break
        
        dcam.cap_stop()
    else:
        print('-NG: Dcam.cap_start() fails with error {}'.format(dcam.lasterr()))


def dcam_live_capturing(iDevice=0):
    """ Capture & show image from HAMAMATSU Camera """
    if Dcamapi.init() is not False:
        dcam = Dcam(iDevice)
        if dcam.dev_open() is not False:
            if dcam.buf_alloc(3) is not False:
                # th = threading.Thread(target=dcamtest_thread_live, args=(dcam,))
                # th.start()
                # th.join()
                dcam_thread_live(dcam)

                #release buffer
                dcam.buf_release()
            else:
                print('-NG: Dcam.buf_alloc(3) fails with error {}'.format(dcam.lasterr()))
            dcam.dev_close()
        else:
            print('-NG: Dcam.dev_open() fails with error {}'.format(dcam.lasterr()))
    else:
        print('-NG: Dcamapi.init() fails with error {}'.format(Dcamapi.lasterr()))

    Dcamapi.uninit()

if __name__ == '__main__':
    dcam_show_device_list()
