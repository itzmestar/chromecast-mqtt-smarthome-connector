# Chromecast MQTT-smarthome connector

Fork of [nohum](https://github.com/nohum)'s [chromecast-mqtt-connector](https://github.com/nohum/chromecast-mqtt-connector) using topic naming convetion from [mqtt-smarthome](https://github.com/mqtt-smarthome/mqtt-smarthome).

## installation

	git clone 
	pip3 install -r requirements.txt

## Usage

Control behaviour by defining values in `config.ini`:

```config
    [mqtt]
    broker_address = 127.0.0.1 
    broker_port = 1883 
    username = username 
    password = pass
```

And run with python3:

	python3 connector.py

## raspberrypi service

Update `User` & `WorkingDirectory` in `chromecast.service` file.
Then perform following steps to install & enable the service on raspberrypi:

    sudo cp chromecast.service /etc/systemd/system/chromecast.service
    sudo systemctl daemon-reload
    sudo systemctl start chromecast.service
    sudo systemctl status chromecast.service
    sudo systemctl enable chromecast.service

To stop the service:

    sudo systemctl stop chromecast.service

## Docker

	docker run -d --net=host -e "MQTT_HOST=10.1.1.100" dersimn/chromecast-mqtt-smarthome-connector

## Discovery and control

Using MQTT you can find the following topics. `FRIENDLY_NAME` is the name used to connect
to each Chromecast.

	python/chromecast/maintenance/_bridge/online -> bool

	python/chromecast/maintenance/FRIENDLY_NAME/online -> bool
	python/chromecast/maintenance/FRIENDLY_NAME/connection_status -> string
	python/chromecast/maintenance/FRIENDLY_NAME/cast_type -> string

	python/chromecast/status/FRIENDLY_NAME/current_app -> string
	python/chromecast/status/FRIENDLY_NAME/volume -> JSON
    python/chromecast/status/FRIENDLY_NAME/media -> JSON 
    python/chromecast/status/FRIENDLY_NAME/player -> JSON
	
    python/chromecast/set/FRIENDLY_NAME/volume -> float
	python/chromecast/set/FRIENDLY_NAME/volume/muted -> bool
	python/chromecast/set/FRIENDLY_NAME/player -> string
	python/chromecast/set/FRIENDLY_NAME/player/position -> int


Change volume using values from `0` to `1.0`:

* Publish e.g. `1.0` to `python/chromecast/set/FRIENDLY_NAME/volume`

Change mute state: publish `false` or `true` to `python/chromecast/set/FRIENDLY_NAME/volume/muted`.

Play something: Publish a json array with two elements (content url and content type) to
`python/chromecast/set/FRIENDLY_NAME/player`, e.g. `["http://your.stream.url.here", "audio/mpeg"]`.
You can also just publish a URL to `player_state` (just as string, not as json array, e.g.
`http://your.stream.url.here`), the application then tries to guess the required MIME type.

For other player controls, simply publish e.g. `RESUME`, `PAUSE`, `STOP`, `SKIP` or `REWIND` to
`python/chromecast/set/FRIENDLY_NAME/player`. Attention: This is case-sensitive!

## Development / Debug

### docker build

	docker build -t chromecast-mqtt-smarthome-connector .

Cross-build (for Raspberry Pi):

    docker buildx create --name mybuilder
    docker buildx use mybuilder
    docker buildx build \
        --platform linux/amd64,linux/arm/v7 \
        -t dersimn/chromecast-mqtt-smarthome-connector \
        -t dersimn/chromecast-mqtt-smarthome-connector:1 \
        -t dersimn/chromecast-mqtt-smarthome-connector:1.3 \
        -t dersimn/chromecast-mqtt-smarthome-connector:1.3.2 \
        --push .
