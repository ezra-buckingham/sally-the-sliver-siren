#!/usr/bin/env python3

import asyncio
from pathlib import Path
from time import sleep
import argparse
import requests
from sliver import *

async def main():
    parser = argparse.ArgumentParser(description='Custom Sliver client that will will emit events and send webhook notifications when new beacons / sessions check in.')
    parser.add_argument('-c', '--sliver_config', type=Path, help='Path to the sliver config to connect with')
    parser.add_argument('-u', '--slack_url', type=str, help='Slack URL to send notifications to' )
    parser.add_argument('-s', '--sleep', default=1, help='Sleep time in between checking for changes in beacons / sessions')

    
    args = parser.parse_args()
    sliver_config = args.sliver_config
    slack_url = args.slack_url
    sleep_time = args.sleep

    if not sliver_config.exists():
        print('Sliver config not found at location provided')
        exit(1)
    

    config = SliverClientConfig.parse_config_file(sliver_config)
    client = SliverClient(config)
    await client.connect()

    original_beacons = await client.beacons()
    original_sessions = await client.sessions()

    while True:
        current_beacons = await client.beacons()
        difference_in_beacons = extract_uuid(
            current_beacons) - extract_uuid(original_beacons)

        current_sessions = await client.sessions()
        difference_in_sessions = extract_uuid(
            current_sessions) - extract_uuid(original_sessions)

        if len(difference_in_beacons) > 0:
            original_beacons = current_beacons

            for new_beacon in difference_in_beacons:
                new_beacon_data = [
                    selected_beacon for selected_beacon in current_beacons if selected_beacon.ID == new_beacon]
                new_beacon_data = new_beacon_data[0]
                post_data = generate_slack_message(new_beacon_data, 'beacon')

                requests.post(slack_url, json=post_data)

        if len(difference_in_sessions) > 0:
            original_sessions = current_sessions

            for new_session in difference_in_sessions:
                new_session_data = [
                    selected_session for selected_session in current_sessions if selected_session.ID == new_session]
                new_session_data = new_session_data[0]
                post_data = generate_slack_message(new_session_data, 'session')

                requests.post(slack_url, json=post_data)

        sleep(sleep)


def extract_uuid(beacon_list):
    beacon_uuids = [beacon.ID for beacon in beacon_list]

    return set(beacon_uuids)


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
