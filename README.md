[![Python checks](https://github.com/vladak/mq2anno/actions/workflows/python-checks.yml/badge.svg)](https://github.com/vladak/mq2anno/actions/workflows/python-checks.yml)

# mq2anno

convert MQTT events to Grafana annotations. Basically each message received on given topic will be converted to Grafana annotation with the message content used as tag. The rest of the message is determined on the fly (time) or using a template.

## Grafana

- Generate API key

## MQTT broker

- Install Mosquito MQTT broker:
```
sudo apt install -y mosquitto mosquitto-clients
cat << EOF | sudo tee /etc/mosquitto/conf.d/local.conf
allow_anonymous true
listener 1883
EOF
sudo systemctl restart mosquitto
systemctl status mosquitto
```
- Test basic MQTT functionality:
```
mosquitto_sub -d -t test
mosquitto_pub -d -t test -m "Hello, World!"
```

## Install and setup

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
- create the `/srv/mq2anno/headers.json` file. This JSON file will contain the headers sent with the Grafna API requests. Use the Grafana API key to setup the `Authorization` header. It may look like this:
```json
{
  "Content-type": "application/json",
  "Authorization": "Bearer <ENTER_THE_API_KEY_HERE>"
}
```
- create the `/srv/mq2anno/payload.json` file. This JSON file can look like this:
```json
{
  "dashboardId":4,
  "tags":["tag1","tag2"],
  "text":"Annotation Description"
}
```
- configure the service: create `/srv/mq2anno/environment` file and setup these environment variables inside:
  - `ARGS`: arguments to the `mq2anno` program
    - the `-H`, `-U` and MQTT broker hostname/port arguments are required
  - the file can look like this (no double quotes):
```
ARGS=-U http://localhost:3000 -t "workmon/blink" -l debug localhost 1883
```
- setup the service (assumes the `pi` user)
```
  sudo cp /srv/mq2anno/mq2anno.service /etc/systemd/system/
  sudo systemctl enable mq2anno
  sudo systemctl daemon-reload  # in case the service file changed
  sudo systemctl start mq2anno
  sudo systemctl status mq2anno
```


