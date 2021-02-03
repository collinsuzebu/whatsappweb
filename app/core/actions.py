import os
import time
import shutil
import threading

from app.core import config
from app.core.requestsvar import gbl
from app.wrapper.webwhatsapi import WhatsAPIDriver, WhatsAPIDriverStatus
from app.core.global_vars import (
    timers,
    drivers,
    semaphores,
    drivers_created_time,
    services
)
from app.core.utils import (
    get_qr_image_path,
    process_image,
    send_qr_email,
    send_to_external_service
)




class RepeatedTimer:
  def __init__(self, interval, function, *args, **kwargs):
    self._timer = None
    self.interval = interval
    self.function = function
    self.args = args
    self.kwargs = kwargs
    self.is_running = False
    self.next_call = time.time()
    self.start()

  def _run(self):
    self.is_running = False
    self.start()
    self.function(*self.args, **self.kwargs)

  def start(self):
    if not self.is_running:
      print("START TIMER")
      self.next_call += self.interval
      self._timer = threading.Timer(self.next_call - time.time(), self._run)
      self._timer.start()
      self.is_running = True

  def stop(self):
    self._timer.cancel()
    self.is_running = False


def init_timer(client_id):
    '''
        Create a timer for client to monitor new whatsapp messages events
    '''
    if client_id in timers and timers[client_id]:
        timers[client_id].start()

    timers[client_id] = RepeatedTimer(
        config.TIME_INTERVAL_NEW_MESSAGES,
        check_new_messages,
        client_id
    )


def set_qr_code(client_id, driver):
    g = gbl()
    img_path = get_qr_image_path(client_id, with_border=False)

    try:
        if (
            driver.get_status() == WhatsAPIDriverStatus.NotLoggedIn or
            driver.get_status() == WhatsAPIDriverStatus.Unknown
            ):

            driver.get_qr(img_path)
            process_image(img_path, client_id)
            send_qr_email(client_id)
            print('QR CODE GOTTEN for client {}'.format(client_id))
            init_timer(client_id)
    except Exception as e:
        print(e)
        return False
    return True


def init_driver(client_id: str) -> WhatsAPIDriver:
    '''
        Initializes a new WhatsappAPIDriver
    '''
    profile_path = config.FIREFOX_CACHE_PATH + '_' + str(client_id)
    if not os.path.exists(profile_path):
        os.makedirs(profile_path)

    driver = WhatsAPIDriver(
        client="remote",
        username=client_id,
        profile=profile_path,
        command_executor=config.SELENIUM_SERVER,
        loadstyles=True,
    )
    driver.wait_for_login()
    set_qr_code(client_id, driver)
    driver.save_firefox_profile()

    return driver


def init_client(client_id: str) -> WhatsAPIDriver:
    '''
        Initializes a driver for new client object and store in global namespace
    '''

    if client_id not in drivers:
        drivers[client_id] = init_driver(client_id)
    return drivers[client_id]




def check_new_messages(client_id):
    """
        Check for new messages and send them to external service/api
    """

    # return if driver is not created or driver is logged out of whatsapp
    if (
        client_id not in drivers
        or not drivers[client_id]
        or not drivers[client_id].is_logged_in()
    ):
        timers[client_id].stop()
        return

    # when new messages are being pulled, acquire a semaphore to prevent other
    # threads from calling the function
    if not acquire_semaphore(client_id, True):
        return

    try:
        # get all unread messages
        contacts = drivers[client_id].get_unread()

        # quickly acknoledge receipt of message to user
        print('PROCESSING MESSAGES IN RES', contacts)
        for msg_obj in contacts:
            msg_obj.chat.send_seen()
        # release semaphore lock
        release_semaphore(client_id)

        url = services[client_id]

        for contact in contacts:
            for message in contact.messages:
                if message.type == 'chat':
                    data = {
                        "chatId": message.sender.id,
                        "body": message.content,
                        "author": message.sender.get_safe_name(),
                        "fromMe": "false",
                        "phone": message.chat_id['user'],
                        "timestamp": str(message.timestamp)
                    }
                    send_to_external_service(url, data)
    except Exception as e:
        print(e)
    finally:
        release_semaphore(client_id)


def acquire_semaphore(client_id: str, cancel_if_locked=False):
    if not client_id:
        return False

    if client_id not in semaphores:
        semaphores[client_id] = threading.Semaphore()
    timeout = 10
    if cancel_if_locked:
        timeout = 0
    sem = semaphores[client_id].acquire(blocking=True, timeout=timeout)
    return sem


def release_semaphore(client_id):
    if not client_id:
        return False

    if client_id in semaphores:
        semaphores[client_id].release()


def delete_client(client_id, preserve_cache):
    """Delete all objects related to client"""

    if client_id in drivers:
        drivers.pop(client_id).quit()
        drivers_created_time.pop(client_id)

        try:
            timers[client_id].stop()
            timers[client_id] = None
            release_semaphore(client_id)
            semaphores[client_id] = None
        except Exception as e:
            print(e)

    if not preserve_cache:
        path = config.FIREFOX_CACHE_PATH + "_" + client_id
        shutil.rmtree(path)


# class RepeatedTimer:
#     def __init__(self, interval, callback, *args, **kwargs):
#         self._interval = interval
#         self._callback = callback
#         self._event = threading.Event()
#         self._thread = None
#         self.args = args
#
#     def start(self) -> bool:
#         self._start = time.time()
#         if self._thread is None:
#             self._event.clear()
#             self._thread = threading.Thread(
#                 target=self._target,
#                 args=self.args
#             )
#             self._thread.start()
#         return True
#
#     def _target(self, client_id) -> None:
#         while not self._event.wait(self._time):
#             self._callback(client_id)
#         self._thread = None
#
#     @property
#     def _time(self) -> int:
#         return self._interval - ((time.time() - self._start) % self._interval)
#
#     @property
#     def is_running(self) -> bool:
#         if self._thread:
#             return True
#         return False
#
#     def stop(self) -> bool:
#         self._event.set()
#         if self._thread is not None:
#             self._thread.join()
#         return True
