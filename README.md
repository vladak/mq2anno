# mq2anno

convert MQTT events to Grafana annotations

- create the `headers.json` file. It may look like this:
```json
{
  "Content-type": "application/json",
  "": ""
}
```
- pre-requisites:
```
sudo apt-get install -y python3-venv
```
- install:
```
sudo mkdir /srv
sudo apt-get install -y git
git clone https://github.com/vladak/mq2anno /srv/mq2anno
cd /srv/mq2anno
python3 -m venv env
. ./env/bin/activate
pip install -r requirements.txt
```
- configure the service: create `/srv/mq2anno/environment` file and setup these environment variables inside:
  - `ARGS`: arguments to the `mq2anno` program
    - the `-H`, `-U` and XXX are required
- setup the service (assumes the `pi` user)
```
  sudo cp /srv/mq2anno/mq2anno.service /etc/systemd/system/
  sudo systemctl enable mq2anno
  sudo systemctl daemon-reload  # in case the service file changed
  sudo systemctl start mq2anno
  sudo systemctl status mq2anno
```


