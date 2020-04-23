from strip import StripController
from settings import mqtt_ip

import paho.mqtt.client as mqtt

class MediaMQTT:
    def __init__(self, mqtt):
        self.mqtt_client = mqtt
        self.strip = StripController()
        self.strip.music()
        self.mqtt_client.subscribe("domos/strip/#")
        self.mqtt_client.message_callback_add('domos/strip/#', self.strip_action)
        self.mqtt_client.message_callback_add('domos/strip/notification', self.notification)


    def strip_action(self, client, userdata, message):
        payload = message.payload.decode()

        if payload == "rainbow":    
            status = self.strip.rainbow()
        if payload == "clock":
            status = self.strip.clock()
        if payload == "music" or payload == "on":
            status = self.strip.music()
        if payload == "off":
            self.strip.stop_current_mode()
            status = False
        
        if status:
            self.mqtt_client.publish('domos/info/strip/mode', payload, retain=True)
            self.mqtt_client.publish('domos/info/strip', 'on' , retain=True)
        else:
            self.mqtt_client.publish('domos/info/strip', 'off', retain=True)
 
    def notification(self, client, userdata, message):
        payload = message.payload.decode()
        self.strip.notification(payload)


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