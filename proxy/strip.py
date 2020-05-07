import threading
import datetime
from dateutil.tz import gettz
import time
import socket

from settings import strip_address


server = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
server.bind(("0.0.0.0",1234))

NLEDS = 74
reverse_strip = False

colors = {"red": [150, 0, 0], "green": [0, 255, 100], "blue": [0, 0, 255], "light_blue": [0, 100, 200],
          "orange": [255, 100, 0], "black": [0, 0, 0], "purple": [255, 0, 200]}


class StripController:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
        self.sock.bind(('0.0.0.0', 54321))
        self.current = None
        self.update_status()

    # modes
    def rainbow(self):
        return self.starthandler(StripRainbow)

    def clock(self):
        return self.starthandler(StripClock)

    def music(self):
        return self.starthandler(StripMusic)

    def notification(self, color=None):
        if not color:
            color = colors["purple"]
        else:
            try:
                color = colors[color]
            except KeyError:
                color = colors["purple"]
                
        if self.current is None:
            self.current = StripNotification(self.sock, color)
            self.current.join()
            self.current = None
        else:
            class_name = self.current.__class__
            self.stop_current_mode()
            self.current = StripNotification(self.sock, color)
            self.current.join()
            self.current = class_name(self.sock)

    # helpers
    def starthandler(self, class_name):
        same = isinstance(self.current, class_name)
        self.stop_current_mode()
        if not same:
            self.current = class_name(self.sock)
            self.update_status()
            return True
        return False

    def stop_current_mode(self):
        if self.current:
            self.current.stop()
            self.current.join()
            self.current = None
        self.update_status()

    def update_status(self):
        if self.current is None:
            status = "off"
        else:
            status = self.current.__class__.__name__.replace("Strip", "")

        # redis_db.set("strip.status", status)
        return status


class Strip(threading.Thread):
    def __init__(self, sckt):
        threading.Thread.__init__(self)
        self.setDaemon(True)

        self.leds = [colors["black"] for i in range(NLEDS)]
        self.sock = sckt
        self.adress = (strip_address, 1234)
        self.event = threading.Event()
        self.start()

    def update_strip(self):
        if reverse_strip:
            leds2send = self._reverse()
        else:
            leds2send = self.leds

        packet = []
        for position in range(NLEDS):

            packet.append(position)
            for i in range(3):
                packet.append(leds2send[position][i])

        bits = bytes(packet)
        try:
            self.sock.sendto(bits, self.adress)
        except OSError:
            pass

    def _reverse(self):
        start = 0
        end = NLEDS - 1
        temp = [colors["black"] for i in range(NLEDS)]
        while start < end:
            temp[start], temp[end] = self.leds[end], self.leds[start]
            start += 1
            end -= 1
        return temp

    def stop(self):
        self.event.set()

    def soft_reset(self):
        self.leds = [colors["black"] for i in range(NLEDS)]
        self.update_strip()

    def hard_reset(self):
        packet = [255]
        pckt = bytes(packet)
        try:
            self.sock.sendto(pckt, self.adress)
        except OSError:
            pass


class StripClock(Strip):
    def __init__(self, sock):
        self.time = [0, 0, 0]
        Strip.__init__(self, sock)

    def hour_marks(self):
        for position in range(-1, 59, 5):
            if self.leds[position] == colors["black"]:
                if position % 15 == 14:
                    self.leds[position] = colors["orange"]
                else:
                    self.leds[position] = colors["red"]

    def update_time(self):
        hours = 0
        minutes = 1
        seconds = 2
        now = datetime.datetime.now(tz=gettz("Europe/Madrid"))
        new_time = [((now.hour % 12) * 5) - 1 + (now.minute // 15), now.minute - 1, now.second - 1]

        if self.time[seconds] != new_time[seconds]:
            self.leds[self.time[seconds]] = colors["black"]
            self.leds[new_time[seconds]] = colors["purple"]

        if self.time[minutes] != new_time[minutes]:
            self.leds[self.time[minutes]] = colors["black"]
        self.leds[new_time[minutes]] = colors["blue"]

        if self.time[hours] != new_time[hours]:
            self.leds[self.time[hours]] = colors["black"]
        self.leds[new_time[hours]] = colors["green"]
        self.time = new_time

    def run(self):
        while not self.event.is_set():
            self.update_time()
            self.hour_marks()
            self.update_strip()
            time.sleep(1)
        self.soft_reset()


class StripRainbow(Strip):
    def __init__(self, sock):
        Strip.__init__(self, sock)

    def run(self):
        while not self.event.is_set():
            for j in range(0, 256, 2):

                for i in range(NLEDS):
                    self.leds[i] = self.wheel((((i * 256) // NLEDS) + j) & 255)
                self.update_strip()
                time.sleep(0.05)
                if self.event.is_set():
                    break

        self.soft_reset()

    @staticmethod
    def wheel(position):
        position = 255 - position
        if position < 85:
            return [255 - position * 3, 0, position * 3]
        if position < 170:
            position -= 85
            return [0, position * 3, 255 - position * 3]
        position -= 170
        return [position * 3, 255 - position * 3, 0]


class StripNotification(Strip):
    def __init__(self, sock, color):
        self.color = color
        Strip.__init__(self, sock)

    def run(self):
        for i in range(NLEDS // 2):
            self.leds[i + 1] = self.color
            self.leds[NLEDS - i - 1] = self.color
            self.update_strip()
            time.sleep(0.05)
        self.soft_reset()


class StripMusic(Strip):
    def __init__(self, sock):
        Strip.__init__(self, sock)

    def run(self):
        while not self.event.is_set():
                data, addr = server.recvfrom(1024) # buffer size is 1024 bytes
                if(len(data) != 0):
                    self.sock.sendto(data,("10.0.5.8",1234))
        self.soft_reset()
