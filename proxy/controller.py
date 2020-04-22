from strip import StripController
from settings import mqtt_ip

import paho.mqtt.client as mqtt

class MediaMQTT:
    def __init__(self, mqtt):
        self.mqtt_client = mqtt
        self.strip = StripController()
        self.strip.rainbow()
        self.mqtt_client.subscribe("domos/strip/#")
        self.mqtt_client.message_callback_add('domos/strip/#', self.strip_action)

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

        if message.payload.decode() == "off":
            self.strip.stop_current_mode()
            self.mqtt_client.publish('domos/info/strip', 'off', retain=True)
            
        if message.topic.split('/')[-1] == "notification":
            color = message.payload.decode()
            self.strip.notification(color)


if __name__ == "__main__":
    mqtt_client = mqtt.Client("proxy")
    mqtt_client.reconnect_delay_set(1, 5)
    mqtt_client.connect(mqtt_ip)
    mqtt = MediaMQTT(mqtt_client)
    try:
        mqtt_client.loop_forever()
    except KeyboardInterrupt:
        pass
    finally:
        mqtt.strip.stop_current_mode()