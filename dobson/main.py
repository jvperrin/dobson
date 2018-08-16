# Dobson, the bot to show information about Ozone.
#
# This will show all OIDs using SNMP for the router:
# snmpwalk -v1 -c public 192.168.0.1
#
# To get a list of connected IPs and MAC addresses:
# snmpwalk -v1 -c public 192.168.0.1 iso.3.6.1.2.1.3.1.1.2.12.1

import sys
import time

from slackclient import SlackClient

import dobson.utils as utils


def rtm_connect(slack_client):
    """Attempt to connect to Slack and reconnect until successful"""
    while not slack_client.rtm_connect(auto_reconnect=True):
        print('Could not connect to Slack RTM, check token/rate limits', file=sys.stderr)
        time.sleep(5)
    print('Connected successfully to Slack RTM')


def fetch_messages(slack_client):
    """Fetch any new messages and process them to potentially respond"""
    try:
        message_list = slack_client.rtm_read()
    except TimeoutError:
        print('Retrieving message from Slack RTM timed out', file=sys.stderr)
        rtm_connect(slack_client)
        return

    if not message_list:
        return

    for message in message_list:
        if 'type' not in message or message['type'] != 'message':
            return

        # Restrict messages to certain channels
        # TODO: Make this more widely available and add authentication
        if message['channel'] not in utils.ALLOWED_CHANNEL_IDS:
            return

        print(message)

        text = message['text']
        lower_text = text.lower()
        # If someone mentions dobson or ozone at the beginning of the message, respond if it's a valid command
        if lower_text.startswith('dobson') or text.startswith('<@{}>'.format(utils.DOBSON_SLACK_ID)):
            if lower_text.endswith('help') or lower_text.endswith('?'):
                respond_help(slack_client, message['channel'])
            if lower_text.endswith('who') or lower_text.endswith('list'):
                respond_users(slack_client, message['channel'])


def respond_help(slack_client, channel):
    """Respond with a help message"""
    slack_client.api_call(
        'chat.postMessage',
        channel=channel,
        text="I am a bot to give you information about ozone (get it?)! Try a command like 'dobson who'",
        as_user=True,
    )


def respond_users(slack_client, channel):
    """Respond with a list of users who are currently at ozone"""
    users = [device.user for device in utils.get_devices()]

    if len(users) > 2:
        reply = '{}, and {} are at ozone'.format(', '.join(users[:-1]), users[-1])
    elif len(users) == 2:
        reply = '{} and {} are at ozone'.format(users[0], users[1])
    elif len(users) == 1:
        reply = '{} is at ozone'.format(users[0])
    else:
        reply = 'Nobody is at ozone'

    slack_client.api_call(
        'chat.postMessage',
        channel=channel,
        text=reply,
        as_user=True,
    )


def main():
    slack_client = SlackClient(utils.SLACK_API_TOKEN)
    rtm_connect(slack_client)

    while True:
        fetch_messages(slack_client)
        time.sleep(1)


if __name__ == '__main__':
    sys.exit(main())
