import dobson.utils as utils


def log_mac_addresses():
    """Logs all mac addresses connected to the router into a file"""
    mac_address = list([mac.lower() for mac in utils.get_mac_addresses()])
    log_str = ' '.join(mac_address)
    with open(utils.MAC_LOG_FILE, 'a') as f:
        f.write(log_str + '\n')


if __name__ == '__main__':
    log_mac_addresses()
