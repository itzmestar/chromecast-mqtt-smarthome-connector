import logging
import json
import mimetypes

# only used for publishing
TOPIC_PREFIX = "chromecast/"
TOPIC_ONLINE_STATUS = TOPIC_PREFIX + "maintenance/%s/online"
TOPIC_CONNECTION_STATUS = TOPIC_PREFIX + "maintenance/%s/connection_status"
TOPIC_CAST_TYPE = TOPIC_PREFIX + "maintenance/%s/cast_type"

TOPIC_CURRENT_APP = TOPIC_PREFIX + "status/%s/current_app"
TOPIC_PLAYER = TOPIC_PREFIX + "status/%s/player"
TOPIC_VOLUME = TOPIC_PREFIX + "status/%s/volume"
TOPIC_MEDIA = TOPIC_PREFIX + "status/%s/media"

# subscribe
TOPIC_COMMAND_VOLUME_LEVEL = TOPIC_PREFIX + "set/%s/volume"
TOPIC_COMMAND_VOLUME_MUTED = TOPIC_PREFIX + "set/%s/volume/muted"
TOPIC_COMMAND_PLAYER_POSITION = TOPIC_PREFIX + "set/%s/player/position"
TOPIC_COMMAND_PLAYER_STATE = TOPIC_PREFIX + "set/%s/player"

STATE_REQUEST_RESUME = "RESUME"
STATE_REQUEST_PAUSE = "PAUSE"
STATE_REQUEST_STOP = "STOP"
STATE_REQUEST_SKIP = "SKIP"
STATE_REQUEST_REWIND = "REWIND"


# play stream has another syntax, not listed here therefore


class MqttChangesCallback:
    def on_volume_mute_requested(self, is_muted):
        pass

    def on_volume_level_relative_requested(self, relative_value):
        pass

    def on_volume_level_absolute_requested(self, absolute_value):
        pass

    def on_player_position_requested(self, position):
        pass

    def on_player_play_stream_requested(self, content_url, content_type):
        pass

    def on_player_pause_requested(self):
        pass

    def on_player_resume_requested(self):
        pass

    def on_player_stop_requested(self):
        pass

    def on_player_skip_requested(self):
        pass

    def on_player_rewind_requested(self):
        pass


class MqttPropertyHandler:
    def __init__(self, mqtt_connection, mqtt_topic_filter, changes_callback):
        self.logger = logging.getLogger("mqtt")
        self.mqtt = mqtt_connection
        self.topic_filter = mqtt_topic_filter
        self.changes_callback = changes_callback
        self.write_filter = {}

    def is_topic_filter_matching(self, topic):
        """
        Check if a topic (e.g.: chromecast/my_device_name/player_state) matches our filter (the name part).
        """
        try:
            return topic.split("/")[2] == self.topic_filter
        except IndexError:
            return False

    def _write(self, topic, value):
        # noinspection PyBroadException
        try:
            if isinstance(value, float):
                value = str(value)
            elif isinstance(value, bool):
                if value:
                    value = "true"
                else:
                    value = "false"
            elif value is None:
                value = ""
            else:
                value = str(value)

            formatted_topic = topic % self.topic_filter

            # filter to prevent writing the same value again until it has changed
            if formatted_topic in self.write_filter and self.write_filter[formatted_topic] == value:
                return

            self.write_filter[formatted_topic] = value
            self.mqtt.send_message(formatted_topic, value)
        except Exception:
            self.logger.exception("value conversion error")

    def write_cast_status(self, app_name, volume_level, is_volume_muted):
        self._write(TOPIC_CURRENT_APP, app_name)
        self.mqtt.send_message(TOPIC_VOLUME % self.topic_filter, json.dumps({'val': volume_level, 'muted': is_volume_muted}))

        self.send_set_vol_message(volume_level, is_volume_muted)

    def send_set_vol_message(self, volume_level, is_volume_muted):
        self.mqtt.send_message(TOPIC_COMMAND_VOLUME_LEVEL % self.topic_filter, volume_level)
        self.mqtt.send_message(TOPIC_COMMAND_VOLUME_MUTED % self.topic_filter, is_volume_muted)

    def write_player_status(self, state, current_time, duration):
        self.mqtt.send_message(TOPIC_PLAYER % self.topic_filter, json.dumps({'val': state, 'position': current_time, 'duration': duration}))

    def send_set_player_message(self):
        pass

    def write_media_status(self, title, album_name, artist, album_artist, track, images, content_type, content_id):
        self.mqtt.send_message(TOPIC_MEDIA % self.topic_filter, json.dumps({
            'title': title,
            'album_name': album_name,
            'artist': artist,
            'album_artist': album_artist,
            'track': track,
            'images': images,
            'content_type': content_type,
            'content_id': content_id
            }))

    def write_connection_status(self, status):
        self._write(TOPIC_CONNECTION_STATUS, status)

    def write_online_status(self, status):
        self._write(TOPIC_ONLINE_STATUS, status)

    def write_cast_data(self, cast_type, friendly_name):
        self._write(TOPIC_CAST_TYPE, cast_type)

    def handle_message(self, topic, payload):
        if isinstance(payload, bytes):
            payload = payload.decode('utf-8')

        payload = str(payload).strip()

        if TOPIC_COMMAND_VOLUME_MUTED % self.topic_filter == topic:
            self.handle_volume_mute_change(payload)
        elif TOPIC_COMMAND_VOLUME_LEVEL % self.topic_filter == topic:
            self.handle_volume_level_change(payload)
        elif TOPIC_COMMAND_PLAYER_POSITION % self.topic_filter == topic:
            self.handle_player_position_change(payload)
        elif TOPIC_COMMAND_PLAYER_STATE % self.topic_filter == topic:
            self.handle_player_state_change(payload)

    def handle_volume_mute_change(self, payload):
        """
        Change volume mute where 1 = muted, 0 = unmuted.
        """

        if payload != "false" and payload != "true":
            return

        self.changes_callback.on_volume_mute_requested(payload == "true")

    def handle_volume_level_change(self, payload):
        """
        Change volume level to either absolute value between 0 .. 1.0
        """

        if len(payload) == 0:
            return

        # noinspection PyBroadException
        try:
            value = float(payload)
        except Exception:
            self.logger.exception("failed decoding requested volume level")
            return

        self.changes_callback.on_volume_level_absolute_requested(value)

    def handle_player_position_change(self, payload):
        """
        Change current player position
        """

        if len(payload) == 0:
            return

        # noinspection PyBroadException
        try:
            # allow sending us floats but we only need the integer and not the decimal part
            value = int(float(payload))
            self.changes_callback.on_player_position_requested(value)
        except Exception:
            self.logger.exception("failed decoding requested position")

    def handle_player_state_change(self, payload):
        if payload == STATE_REQUEST_PAUSE:
            self.changes_callback.on_player_pause_requested()
        elif payload == STATE_REQUEST_RESUME:
            self.changes_callback.on_player_resume_requested()
        elif payload == STATE_REQUEST_STOP:
            self.changes_callback.on_player_stop_requested()
        elif payload == STATE_REQUEST_SKIP:
            self.changes_callback.on_player_skip_requested()
        elif payload == STATE_REQUEST_REWIND:
            self.changes_callback.on_player_rewind_requested()
        else:
            if len(payload) == 0:
                return

            # noinspection PyBroadException
            try:
                if payload[0] != "[":
                    url = payload
                    mime_data = mimetypes.guess_type(url, strict=False)
                    found_mime_type = None
                    if mime_data is not None:
                        found_mime_type = mime_data[0]

                    if found_mime_type is None:
                        self.logger.warning("no mime type found")

                    self.changes_callback.on_player_play_stream_requested(url, found_mime_type)
                else:
                    data = json.loads(payload)
                    if not isinstance(data, list) or len(data) != 2:
                        raise AssertionError("data must be array and must possess two elements (url, content type)")

                    self.changes_callback.on_player_play_stream_requested(data[0], data[1])
            except Exception:
                self.logger.exception("failed decoding requested play stream data: %s" % payload)
