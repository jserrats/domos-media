from spotify import next_song, prev_song, playpause, get_current_song
import threading
import time
import __main__
from strip import StripController
import telogram
import settings
import paho.mqtt.client as mqtt
import subprocess

spotify_actions = {"next": next_song, "previous": prev_song, "play": playpause, "get": get_current_song}


class SongPublisher(threading.Thread):
    def __init__(self, mqtt):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.mqtt = mqtt
        self.start()
        self.song = ''

    def run(self):
        while True:
            time.sleep(1)
            author, song = get_current_song()
            if song != self.song:
                self.song = song
                self.mqtt.publish("domos/info/media/spotify/current", author + '\n' + song, retain=True)


class MediaMQTT:
    def __init__(self, mqtt):
        self.mqtt_client = mqtt
        self.strip = StripController(self.mqtt_client)
        self.strip.music()
        self.mqtt_client.subscribe("domos/strip/#")
        self.mqtt_client.subscribe("domos/media/#")
        self.mqtt_client.message_callback_add('domos/media/spotify', self.spotify_action)
        self.mqtt_client.message_callback_add('domos/media/off', self.off)
        self.mqtt_client.message_callback_add('domos/strip/#', self.strip_action)
        self.mqtt_client.publish('domos/info/strip', 'rainbow', retain=True)

    def off(self, client, userdata, message):
        subprocess.call(["systemctl poweroff"])

    def spotify_action(self, client, userdata, message):
        spotify_actions[message.payload.decode()]()
        time.sleep(0.2)
        author, song = get_current_song()
        self.mqtt_client.publish("domos/info/media/spotify/current", author + '\n' + song, retain=True)

    def strip_action(self, client, userdata, message):
        if message.payload.decode() == "rainbow":
            self.strip.rainbow()
            self.mqtt_client.publish('domos/info/strip', 'rainbow', retain=True)
        if message.payload.decode() == "clock":
            self.strip.clock()
            self.mqtt_client.publish('domos/info/strip', 'clock', retain=True)

        if message.payload.decode() == "music":
            self.strip.music()
            self.mqtt_client.publish('domos/info/strip', 'music', retain=True)

        if message.payload.decode() == "music_effect":
            self.strip.music_effect()
        if message.payload.decode() == "off":
            self.strip.stop_current_mode()
            self.mqtt_client.publish('domos/info/strip', 'off', retain=True)
        if message.topic.split('/')[-1] == "notification":
            color = message.payload.decode()
            self.strip.notification(color)


if __name__ == "__main__":
    telogram.init(settings.telegram_id, settings.telegram_token)
    mqtt_client = mqtt.Client(__main__.__file__)
    mqtt_client.reconnect_delay_set(1, 5)
    mqtt_client.connect("mqtt.lan")
    updater = SongPublisher(mqtt_client)
    mqtt = MediaMQTT(mqtt_client)
    try:
        mqtt_client.loop_forever()
    except KeyboardInterrupt:
        pass
    finally:
        mqtt.strip.stop_current_mode()
