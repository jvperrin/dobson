# Dobson, the bot to show information about Ozone.
#
# This will show all OIDs using SNMP for the router:
# snmpwalk -v1 -c public 192.168.0.1
#
# To get a list of connected IPs and MAC addresses:
# snmpwalk -v1 -c public 192.168.0.1 iso.3.6.1.2.1.3.1.1.2.12.1
import random
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
            elif lower_text.endswith('who') or lower_text.endswith('list'):
                respond_users(slack_client, message['channel'], message)
            elif lower_text.endswith('list unknown'):
                respond_users(slack_client, message['channel'], message, list_all=True)


def respond_help(slack_client, channel):
    """Respond with a help message"""
    slack_client.api_call(
        'chat.postMessage',
        channel=channel,
        text="I am a bot to give you information about ozone (get it?)! Try a command like 'dobson who'",
        as_user=True,
    )


def respond_users(slack_client, channel, message, list_all=False):
    """Respond with a list of users who are currently at ozone"""
    users = [device.user for device in utils.get_devices()]
    unknown = list(utils.get_unknown_mac_addresses())

    final_response = UserResponse(users, unknown, message, list_all).random_response()

    slack_client.api_call(
        'chat.postMessage',
        channel=channel,
        text=final_response,
        as_user=True,
    )


class UserResponse:
    """
    A helper class to handle crafting response strings to dobson queries
    """

    def __init__(self, users, unknown, message, list_all):
        self.users = users
        self.unknown = unknown
        self.message = message
        self.list_all = list_all

    def random_response(self):
        """Returns a random response from our response methods"""
        return random.choice([self.response1])()

    def response1(self):
        """
        Sample responses:

        Nobody is at ozone, but there is 1 unknown device...
        Sean is at ozone, along with the following unknown devices: 000 and 111
        """
        # reply containing who is at ozone, e.g. "A, B and C are at ozone"
        if self.users:
            reply = '{list_formatted} {is_are} at ozone'.format(**UserResponse.grammar_helper(self.users))
        else:
            reply = 'Nobody is at ozone'

        # Add unknown MAC Addresses to the response
        if self.unknown:
            unknown_prefix = ', ' + ('along with ' if self.users else ' but there {is_are} ')
            if self.list_all:
                unknown_reply = unknown_prefix + 'the following unknown device{s?}: {list_formatted}'
                unknown_reply = unknown_reply.format(**UserResponse.grammar_helper(self.unknown))
            else:
                unknown_reply = unknown_prefix + '{num} unknown device{s?}{ellipsis}'
                unknown_reply = unknown_reply.format(**UserResponse.grammar_helper(
                    self.unknown,
                    ellipsis='...' if not self.users else '',
                ))
        else:
            unknown_reply = '.'

        return reply + unknown_reply

    @staticmethod
    def grammar_helper(items, **kwargs):
        """
        Takes in a list of items and returns a dictionary mapping keywords to strings for use in format strings.

        For example, if we pass in a list with 1 element, the key 'is_are' would be 'is', and a list with 2 or more
        elements would be 'are'. This enables us to use format strings such as "{list_formatted} {is_are} home"

        >>> "There {is_are} {num} device{s?} connected".format(**grammar_helper(['sean', 'jason', 'nikhil']))
        "There are 3 devices connected"


        The list of keywords returned:
        * is_are: either the string 'is' or 'are'
        * num: the number of elements as a string, e.g. '2'
        * s?: either the string 's' or the empty string ('')
        * list_formatted: the output of calling list_to_str on items
        """
        return {
            'is_are': 'is' if len(items) == 1 else 'are',
            'num': '{:,}'.format(len(items)),
            's?': '' if len(items) == 1 else 's',
            'list_formatted': UserResponse.list_to_str(items),
            **kwargs,
        }

    @staticmethod
    def list_to_str(lst):
        """
        Returns a comma separated string for the passed list
        >>> list_to_str(['sean', 'jason', 'nikhil'])
        'sean, jason and nikhil'
        >>> list_to_str(['sean', 'jason'])
        'sean and jason'
        >>> list_to_str(['sean'])
        'sean'
        >>> list_to_str([])
        ''
        """
        if len(lst) > 2:
            return '{}, and {}'.format(', '.join(lst[:-1]), lst[-1])
        elif len(lst) == 2:
            return '{} and {}'.format(lst[0], lst[1])
        elif len(lst) == 1:
            return '{}'.format(lst[0])
        else:
            return ''


def main():
    slack_client = SlackClient(utils.SLACK_API_TOKEN)
    rtm_connect(slack_client)

    while True:
        fetch_messages(slack_client)
        time.sleep(1)


if __name__ == '__main__':
    sys.exit(main())
