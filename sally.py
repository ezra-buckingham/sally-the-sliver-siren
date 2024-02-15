#!/usr/bin/env python3

import asyncio, os, argparse, requests, yaml
from pathlib import Path
from time import sleep
from sliver import *

async def main():
    parser = argparse.ArgumentParser(description='Custom Sliver client that will will emit events and send webhook notifications when new beacons / sessions check in.')
    parser.add_argument('-c', '--config', type=Path, help='Path to sally config file (which will immediately take effect as changes to Sally)')
    parser.add_argument('-S', '--sliver_config', default=None, type=Path, help='Path to the sliver config to connect with')
    parser.add_argument('-u', '--url', default=None, type=str, help='Webhook URL to send notifications to' )
    parser.add_argument('-p', '--provider', default=None, type=str, help='Slack or Teams' )
    parser.add_argument('-s', '--sleep', type=int, default=10, help='Sleep time in between checking for changes in beacons / sessions')

    args = parser.parse_args()
    sally_config = args.config
    sliver_config = args.sliver_config
    provider = args.provider
    webhook_url = args.url
    sleep_time = args.sleep

    # Flag to represent if we are using a config file
    using_config = False

    if sally_config and not sliver_config and not sliver_config:
        using_config = True
        sliver_config, provider, webhook_url, sleep_time = read_config(sally_config)

    if not os.path.exists(sliver_config):
        print('[X] Sliver config not found at ' + str(sliver_config))
        exit(1)

    config = SliverClientConfig.parse_config_file(sliver_config)
    client = SliverClient(config)

    print('[*] Connecting to Sliver Server...')
    await client.connect()
    print('[*] Connected to Sliver Server!')

    print('[*] Getting current Sliver beacons')
    original_beacons = await client.beacons()
    print('[*] Getting current Sliver sessions')
    original_sessions = await client.sessions()


    while True:
        current_beacons = await client.beacons()
        difference_in_beacons = extract_uuid(
            current_beacons) - extract_uuid(original_beacons)

        current_sessions = await client.sessions()
        difference_in_sessions = extract_uuid(
            current_sessions) - extract_uuid(original_sessions)

        if len(difference_in_beacons) > 0:
            print('[*] Found new beacons')
            original_beacons = current_beacons

            for new_beacon in difference_in_beacons:
                new_beacon_data = [
                    selected_beacon for selected_beacon in current_beacons if selected_beacon.ID == new_beacon]
                new_beacon_data = new_beacon_data[0]
                if str(provider).lower() == 'teams':
                    post_data = generate_teams_message(new_beacon_data, 'beacon')
                elif str(provider).lower() == 'slack':
                    post_data = generate_slack_message(new_beacon_data, 'beacon')
                print(f'[*] Sending message about beacon {new_beacon}')
                try:
                    resp = requests.post(webhook_url, json=post_data)
                    print(f'[*] Sent message: HTTP ({resp.status_code})')

                except:
                    print(f'[X] Something went wrong when sending webhook message, check the URL used')
                
            
        else:
            print('[*] No new beacons found')

        if len(difference_in_sessions) > 0:
            print('[*] Found new sessions')
            original_sessions = current_sessions

            for new_session in difference_in_sessions:
                new_session_data = [
                    selected_session for selected_session in current_sessions if selected_session.ID == new_session]
                new_session_data = new_session_data[0]
                if str(provider).lower() == 'teams':
                    post_data = generate_teams_message(new_session_data, 'session')
                elif str(provider).lower() == 'slack':
                    post_data = generate_slack_message(new_session_data, 'session')

                print(f'[*] Sending message about session {new_session}')
                try:
                    resp = requests.post(webhook_url, json=post_data)
                    print(f'[*] Sent message: HTTP ({resp.status_code})')

                except:
                    print(f'[X] Something went wrong when sending webhook message, check the URL used')
            
        else:
            print('[*] No new sessions found')

        print(f'[*] Sleeping for { sleep_time } seconds')
        sleep(sleep_time)

        # Get new config values
        if using_config:
            sliver_config, provider, webhook_url, sleep_time = read_config(sally_config)

   

def read_config(config_path):
    config_file = Path(config_path).read_text()
    config_file_yaml = yaml.safe_load(config_file)

    return config_file_yaml['sliver_config'], config_file_yaml['provider'], config_file_yaml['url'], config_file_yaml['sleep_time']


def extract_uuid(beacon_list):
    beacon_uuids = [beacon.ID for beacon in beacon_list]

    return set(beacon_uuids)

def generate_teams_message(data, type='beacon'):
    
    header_text = '🚨  New Sliver '
    
    if type == 'beacon':
        header_text += 'Beacon'
    elif type == 'session':
        header_text += 'Session'
    else:
        header_text += 'Event'

    post_data = {
    "@type": "MessageCard",
    "@context": "http://schema.org/extensions",
    "themeColor": "0076D7",
    "summary": header_text,
    "sections": [{
        "activityTitle": header_text,
        "activitySubtitle": "C2 Domain: " + data.ActiveC2,
        "activityImage": "https://images.bishopfox.com/prod-1437/Images/global/main-menu/poly-fox-graphic.png",
        "facts": [{
            "name": "Hostname",
            "value": data.Hostname
        }, {
            "name": "Username",
            "value": data.Username
        }, {
            "name": "Process ID",
            "value": data.PID
        }, {
            "name": "OS",
            "value": data.OS
        }],
        "markdown": "true"
    }]
    }
    return post_data

def generate_slack_message(data, type='beacon'):
    header_text = '🚨  New Sliver '

    if type == 'beacon':
        header_text += 'Beacon'
    elif type == 'session':
        header_text += 'Session'
    else:
        header_text += 'Event'

    post_data = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": header_text,
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"```{ data }```"
                }
            }
        ]
    }

    return post_data


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
