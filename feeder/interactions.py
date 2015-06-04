# coding: utf-8

"""
handles interactions with the twitter API.
"""
from __future__ import print_function
from __future__ import unicode_literals


import re
import os
import time
import threading

import twittertools

from twitter.api import Twitter, TwitterError, TwitterHTTPError
from twitter.stream import TwitterStream, Timeout, HeartbeatTimeout, Hangup
from twitter.oauth import OAuth


# see https://dev.twitter.com/streaming/overview/connecting
INITIAL_BACKOFF_DURATION = 60  # seconds

class TwitterHandler(object):

    """wraps twitter API calls and tracks related state"""

    def __init__(self, auth):
        super(TwitterHandler, self).__init__()
        self.auth = auth
        self.api = self.load_twitter()
        self.stream = self.load_stream()
        self.last_mention = None
        self.screen_name = 'pypoet'
        self.seen_users = set()
        self.rate_limit_remaining = 200
        self.rate_limit_reset = time.time()
        self.chill_duration = INITIAL_BACKOFF_DURATION
        self.chill_until = 0
        self.thread = None
        self._userstweets = None

    # this is set in a background thread so we check thread status before touching
    # this could easily be using a lock or something
    @property
    def userstweets(self):
        if self.thread and self.thread.isAlive():
            return None
        elif isinstance(self._userstweets, list):
            result = list(self._userstweets)
            self._userstweets = None
            return result


    def load_twitter(self):
        return Twitter(auth=self.auth, api_version='1.1')

    def load_stream(self):
        params = {'replies': 'all', 'with': 'user'}
        stream_iter = TwitterStream(
            auth=self.auth,
            block=False,
            domain='userstream.twitter.com').user(**params)
        return stream_iter

    def fetch_posts(self, user_name, count=200):
        max_items = 200
        tweets = list()

        params = {'screen_name': user_name,
                  'trim_user': 1, 'count': min(max_items, count)}
        # we get an array of length 1 when we're out of entries
        posts = [None, None]
        while len(posts) > 1 and self.rate_limit_remaining > 0:
            posts = self.api.statuses.user_timeline(**params)
            self.update_rate_limit(posts)
            self.chill_duration = INITIAL_BACKOFF_DURATION
            print('rate limit remaining: %d' % posts.rate_limit_remaining)
            ids = [int(p.get('id_str')) for p in posts]
            # had a weird crash here?
            if len(ids) == 0:
                break
            next_id = min([int(p.get('id_str')) for p in posts])
            params['max_id'] = next_id
            tweets.extend(posts)
        return tweets

    def new_user_events(self):
        """fetch new items in the user stream"""
        events = list()
        while True:
            event = self.stream.next()
            if event != None:
                # print(event)
                events.append(event)
            else:
                break
        return events

    def prune_mention(self, tweet):
        dict_template = {
            "text": True,
            'id_str': True,
            "user": {"screen_name": True, "name": True},
            "entities": {"user_mentions": {'screen_name': True}}}
        pruned = twittertools.prune_dict(tweet, dict_template)
        pruned['mentions'] = [p.get('screen_name', '') for p in
                              pruned.get('entities').get('user_mentions')]
        del pruned['entities']
        return pruned

    def process_user_events(self):
        """
        handle mentions etc. if we're rate limited, return the time
        until the rate limit resets. (this is not code i'm proud of)
         """
        if self.chill_until >= time.time():
            return self.chill_until - time.time()
        if not self.thread or not self.thread.isAlive():
            self.thread = threading.Thread(target=self._process_events)
            self.thread.start()


    def _process_events(self):
        usertweets = list()

        for event in self.new_user_events():
            tweet = event.get('direct_message') or event
            text = tweet.get('text', '')
            user = re.search(r'use @([a-z0-9_]{1,15})', text, flags=re.I)
            if user:
                user = user.group(1)
                if user in self.seen_users:
                    print('skipping user @%s' % user)
                    continue
                else:
                    self.seen_users.add(user)
                    print(text)
                    print("using @%s" % user)
                    try:
                        tweets = self.fetch_posts(user)
                        usertweets.append((user, tweets))
                    except TwitterHTTPError as err:
                        if err.e.code == 420:
                            print('~~~~ ERROR 420 ~~~~')
                            self.chill_out()
                        print("error error error")
                        msg = "an unknown error occured. :("
                        if err.e.code == 401:
                            msg = "unable to access @%s. Is it a private account?" % user
                        elif err.e.code == 404:
                            msg = "the use @%s doesn't appear to exist." % user
                        self.reply(event, msg)
                        continue
        self._userstweets = usertweets

    def update_rate_limit(self, response):
        self.rate_limit_remaining = response.rate_limit_remaining
        self.rate_limit_reset = response.rate_limit_reset


    def chill_out(self):
        self.chill_until = time.time() + self.chill_duration
        self.chill_duration *= 2


    def reply(self, event, message):
        if event.get('direct_message'):
            user = event.get('direct_message').get('sender').get('screen_name')
            self.api.direct_messages.new(user=user, text=message)
        else:
            user = event.get('user', {}).get('screen_name')
            if user:
                self.api.statuses.update(
                    status="@%s %s" % (user, message))

    # def manual_fetch_new_mentions(self):
    #     params = {'count': 200}
    #     if self.last_mention:
    #         params['since_id'] = self.last_mention
    #     mentions = self.api.statuses.mentions_timeline(**params)
    #     if len(mentions):
    #         self.last_mention = max(int(m.get('id_str')) for m in mentions)
    #     users = [m.get('entities').get('user_mentions') for m in mentions]
    #     users = [m for m in users if len(m)]
    #     print(users)


def main():
    t = TwitterHandler()
    while True:
        t.process_user_events()
        # events = t.new_user_events()
        # for e in events:
        #     # print(e.get('text'))
        time.sleep(1)

    # return fetch_posts('cmyr')
    # import argparse
    # parser = argparse.ArgumentParser()
    # parser.add_argument('-o', '--outpath', type=str, default=output_url, help="set outpath")
    # parser.add_argument('-c', '--count', type=int, default=20, help='number of items to save')
    # args = parser.parse_args()
    # fetch_recent_posts(**vars(args))


if __name__ == "__main__":
    main()
