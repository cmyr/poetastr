import time
import os
import sys

from twitter.api import Twitter
from twitter.oauth import OAuth
import twittertools

DEFAULT_INTERVAL = 10*60


def monitor(auth, monitor_file, user, interval=10*60, debug=False):
    interval = interval or DEFAULT_INTERVAL
    if not os.path.exists(monitor_file):
        raise Exception('monitor path %s does not exist' % monitor_file)
    print('will notify user %s if file %s is unmodified within %d seconds' %
          (user, monitor_file, interval))
    while True:
        if debug:
            print('sleeping for %d' % interval)
        time.sleep(interval)
        lastmod = os.path.getmtime(monitor_file)
        if time.time() - lastmod > interval:
            if debug:
                print('notifying user')
            twitter = Twitter(auth=auth, api_version='1.1')
            twitter.direct_messages.new(
                user=user,
                text='monitor of %s missed update %s' % (
                    monitor_file, time.strftime("%b %d, %H:%M:%S")))
        elif debug:
            print('file modified %0.1f ago, continuing' % (time.time() - lastmod))


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('auth', type=str, help="path to twitter auth token")
    parser.add_argument('monitor_file', type=str, help="file to monitor")
    parser.add_argument('-u', '--user', type=str, help="twitter username of user to notify")
    parser.add_argument('-i', '--interval', type=int, help="time (in seconds) betweeen words")
    parser.add_argument(
        '-d', '--debug', action='store_true', help="optionally print more verbose messages")
    args = parser.parse_args()

    # the OAuth object in the twitter module has different positional arguments
    # then the requests OAuth module used in my own streaming implementation
    creds = twittertools.load_auth(args.auth, raw=True)
    auth = OAuth(creds[2], creds[3], creds[0], creds[1])
    return sys.exit(monitor(
        auth, args.monitor_file, user=args.user, interval=args.interval, debug=args.debug))


if __name__ == "__main__":
    main()
