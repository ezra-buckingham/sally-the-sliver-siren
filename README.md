# Sally the Slier Siren

A custom sliver client that will send slack notifications upon new beacons / sessions that check in.

## Usage

To use Sally, first install all dependencies using `pip`:

```bash
pip3 install -r requirements.txt
```

Once all dependencies are installed, you can then run the python script (which will run continuously).

```
usage: sally.py [-h] [-c SLIVER_CONFIG] [-u SLACK_URL] [-s SLEEP]

Custom Sliver client that will will emit events and send webhook notifications when new beacons / sessions check in.

optional arguments:
  -h, --help            show this help message and exit
  -c SLIVER_CONFIG, --sliver_config SLIVER_CONFIG
                        Path to the sliver config to connect with
  -u SLACK_URL, --slack_url SLACK_URL
                        Slack URL to send notifications to
  -s SLEEP, --sleep SLEEP
                        Sleep time in between checking for changes in beacons / sessions
```

## Running Continuously

Since this is just a python script, you can choose to install it as a service and run it continuously that way OR you can use a `tmux` / `screen` session to run it. If you want to go the service route, I have an example [service file](./service/sally.service) included in this repo.

