# doorman
Control SESAME3 from Homebridge by MQTT (support over TLS)

## Required
- [SESAME3](https://jp.candyhouse.co/)
- SESAME3 Wi-Fi module
- MQTT broker (e.g. mosquitto)
- [Homebridge](https://homebridge.io/)
    - [Homebridge MQTT-Thing](https://github.com/arachnetech/homebridge-mqttthing)

## Preparation
- Get API_KEY and CLIENT_ID from [SESAME3 Dashboard](https://dash.candyhouse.co/)
- Get UUID and Secret Key from SESAME3 app
- (if MQTT over TLS) Genarate CA-key file, Cert-key and Key file

## Installation
```bash
git clone git@github.com:jp7eph/doorman.git
cd doorman
# install dependence packages
pip3 install -r requirements.txt
# make config file for deployment
cp config_sample.yaml config.yaml
# suit config file to your environment.
vi config.yaml
```

## Usage
```bash
usage: DOORMAN.py [-h] [-c CONFIG_FILE] [-s SCHEMA_FILE]

Control SESAME3 from Homebridge by MQTT

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG_FILE, --config-file CONFIG_FILE
                        the path to YAML config file. If not specified, defaut
                        path(./config.yaml).
  -s SCHEMA_FILE, --schema-file SCHEMA_FILE
                        the path to schema file for YAML validation. If not
                        specified, defaut path(./schema.yaml).
```

## Manage as systemd service
```bash
sudo ln -s ./systemd/doorman.service /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl start doorman.service
# start doorman automatically when system start up
sudo systemctl enable doorman.service
```