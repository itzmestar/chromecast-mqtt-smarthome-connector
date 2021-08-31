import os
import configparser
import logging


class Config:

    def __init__(self, filename):
        self.config = configparser.ConfigParser()
        self.logger = logging.getLogger("config")

        self.logger.info("config file path: %s" % filename)

        if os.path.isfile(filename):
            self.logger.info("config file has been found")
            self.config.read(filename)
        else:
            self.logger.warn("config file has not been found")
        self.addr = self.config.get('mqtt', 'broker_address', fallback="127.0.0.1")
        self.port = self.config.getint('mqtt', 'broker_port', fallback=1883)
        self.user = self.config.getboolean('mqtt', 'username', fallback=False)
        self.password = self.config.get('mqtt', 'password', fallback=None)
        self.cafile = self.config.get('mqtt', 'cafile', fallback=None)

    def get_mqtt_broker_address(self):
        return self.addr

    def get_mqtt_broker_port(self):
        return self.port

    def get_mqtt_broker_use_auth(self):
        return self.user and self.password

    def get_mqtt_broker_username(self):
        return self.user

    def get_mqtt_broker_password(self):
        return self.password

    def get_mqtt_client_cafile(self):
        return self.cafile
