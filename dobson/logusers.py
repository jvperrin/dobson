import datetime

import dobson.utils as utils


def log_mac_addresses():
    """Logs all mac addresses connected to the router into a file"""
    log_str = ' '.join(utils.get_mac_addresses())
    this_minute = datetime.datetime.now().replace(second=0, microsecond=0).isoformat()
    with open(utils.MAC_LOG_FILE, 'a') as f:
        f.write('{} {}\n'.format(this_minute, log_str))


if __name__ == '__main__':
    log_mac_addresses()
