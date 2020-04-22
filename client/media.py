from settings import mqtt_ip
from music_animation.visualization import microphone, microphone_update, next_animation
import threading
import paho.mqtt.client as mqtt

class StripMusic(threading.Thread):
    def __init__(self):
        self.run()

    def run(self):
        microphone.start_stream(microphone_update)

    def effect(self):
        next_animation()

class MediaMQTT:
    def __init__(self, mqtt):
        self.mqtt_client = mqtt
        self.mqtt_client.message_callback_add('domos/strip/#', self.strip_action)
        self.strip = StripMusic()

    def strip_action(self, client, userdata, message):
        if message.payload.decode() == "music_effect":
            self.strip.effect()
            

if __name__ == "__main__":
    mqtt_client = mqtt.Client("media")
    mqtt_client.reconnect_delay_set(1, 5)
    mqtt_client.connect(mqtt_ip)
    mqtt = MediaMQTT(mqtt_client)
    try:
        mqtt_client.loop_forever()
    except KeyboardInterrupt:
        pass
    finally:
        mqtt.strip.stop_current_mode()
