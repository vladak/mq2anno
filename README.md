[![Python checks](https://github.com/vladak/mq2anno/actions/workflows/python-checks.yml/badge.svg)](https://github.com/vladak/mq2anno/actions/workflows/python-checks.yml)

# mq2anno

convert MQTT events to Grafana annotations. Basically each message received on given topic will be converted to Grafana annotation with the message content used as tag. The rest of the message is determined on the fly (time) or using a template.

Assumes working MQTT broker such as [Mosquitto](https://github.com/eclipse/mosquitto).

## Grafana

- Generate API key in the Configuration -> API keys 

## Install

- pre-requisites:
```
sudo apt-get install -y python3-venv
```
- install (assumes the `pi` user and group):
```
[ -d /srv ] || sudo mkdir /srv
sudo mkdir /srv/mq2anno
sudo chown pi:pi /srv/mq2anno
sudo apt-get install -y git
git clone https://github.com/vladak/mq2anno /srv/mq2anno
cd /srv/mq2anno
python3 -m venv env
. ./env/bin/activate
pip install -r requirements.txt
```

## Configuration

- create the `/srv/mq2anno/headers.json` file. This JSON file will contain the headers sent with the Grafna API requests. Use the Grafana API key to setup the `Authorization` header. It may look like this:
```json
{
  "Content-type": "application/json",
  "Authorization": "Bearer <ENTER_THE_API_KEY_HERE>"
}
```
- create the `/srv/mq2anno/config.json` file. This JSON is keyed by MQTT topic. The value is a dictionary that must contain `dashboard` value.
Example of the configuration can look like this:
```json
{
  "foo/bar": {
    "dashboardUID": "jcIIG-07z",
    "tags": ["tag1", "tag2"],
    "text": "Annotation Description"
  }
}
```

This configuration matches the key/values of the [Grafana Annotation API](https://grafana.com/docs/grafana/latest/developers/http_api/annotations/#create-annotation).
The time values will be added automatically.
The list of tags, will be augmented or created from scratch (if it is not configured) with the tags received in the MQTT message for given topic.

The payload sent to the MQTT topics should contain non-empty list of tags, e.g.:
```json
{"annotation": true, "tags": ["foo", "bar"]}
```

Messages with missing `tags` or `annotation` will be ignored. The `annotation` key allows to reuse the same topic for multiple message types.

## Setup

- configure the service: create `/srv/mq2anno/environment` file and setup these environment variables inside:
  - `ARGS`: arguments to the `mq2anno` program
    - the `-H`, `-U` and MQTT broker hostname/port arguments are required
  - the file can look like this (no double quotes):
```
ARGS=-U http://localhost:3000 -c /srv/mq2anno/config.json -l debug localhost 1883
```
- setup the service (assumes the `pi` user)
```
  sudo cp /srv/mq2anno/mq2anno.service /etc/systemd/system/
  sudo systemctl enable mq2anno
  sudo systemctl daemon-reload  # in case the service file changed
  sudo systemctl start mq2anno
  sudo systemctl status mq2anno
```


