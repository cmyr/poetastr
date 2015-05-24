# coding: utf-8

"""
handles interactions with the twitter API.
"""
from __future__ import print_function
from __future__ import unicode_literals


import json
import functools
import re
import os
import multiprocessing
import Queue
import time
from collections import deque
import twittertools

from twitter.api import Twitter, TwitterError, TwitterHTTPError
from twitter.stream import TwitterStream, Timeout, HeartbeatTimeout, Hangup
from twitter.oauth import OAuth

from twittercreds import (
    CONSUMER_KEY, CONSUMER_SECRET, ACCESS_KEY, ACCESS_SECRET)


class StreamHandler(object):

    """
    handles twitter stream connections. Buffers incoming tweets and
    acts as an iter.
    """

    def __init__(self,
                 buffersize=100,
                 timeout=90,
                 languages=['en'],
                 auth=None
                 ):
        self.buffersize = buffersize
        self.timeout = timeout
        self.languages = languages
        self.stream_process = None
        self.auth = auth
        self.queue = multiprocessing.Queue()
        self._buffer = deque()
        self._should_return = False
        self._iter = self.__iter__()
        self._start_time = time.time()
        self._last_message_check = self._start_time

    def __iter__(self):
        """
        the connection to twitter is handled in another process
        new tweets are added to self.queue as they arrive.
        on each call to iter we move any tweets in the queue to a fifo buffer
        this makes keeping track of the buffer size a lot cleaner.
        """
        while 1:
            if self._should_return:
                print('breaking iteration')
                raise StopIteration
            while 1:
                # add all new items from the queue to the buffer
                try:
                    self._buffer.append(self.queue.get_nowait())
                except Queue.Empty:
                    break
            try:
                if len(self._buffer):
                    # if there's a buffer element return it
                    yield self._buffer.popleft()
                else:
                    yield None
                    continue
            except Queue.Empty:
                print('queue timeout')
        print('exiting iter loop')

    def next(self):
        return self._iter.next()

    def start(self):
        """
        creates a new thread and starts a streaming connection.
        If a thread already exists, it is terminated.
        """
        self._should_return = False
        print('creating new server connection')
        if self.stream_process is not None:
            print('terminating existing server connection')
            self.stream_process.terminate()
            if self.stream_process.is_alive():
                pass
            else:
                print('thread terminated successfully')

        self.stream_process = multiprocessing.Process(
            target=self._run,
            args=(self.queue,
                  self.languages,
                  self.auth))
        self.stream_process.daemon = True
        self.stream_process.start()

        print('created process %i' % self.stream_process.pid)

    def close(self):
        """
        terminates existing connection and returns
        """
        self._should_return = True
        if self.stream_process:
            self.stream_process.terminate()
        print("\nstream handler closed with buffer size %i" %
              (self.bufferlength()))

    def bufferlength(self):
        return len(self._buffer)

    def _run(self, queue, languages, auth):
        """
        handle connection to streaming endpoint.
        adds incoming tweets to queue.
        runs in own process.
        """
        params = {'replies': 'all'}
        stream_iter = TwitterStream(
            auth=auth,
            domain='userstream.twitter.com').user(**params)

        for tweet in stream_iter:
            if not isinstance(tweet, dict):
                continue
            if tweet.get('text'):
                try:
                    queue.put(tweet, block=False)
                except Queue.Full:
                    pass


class TwitterHandler(object):

    """wraps twitter API calls and tracks related state"""

    def __init__(self):
        super(TwitterHandler, self).__init__()
        self.auth = OAuth(
            ACCESS_KEY, ACCESS_SECRET, CONSUMER_KEY, CONSUMER_SECRET)
        self.api = self.load_twitter()
        self.stream = self.load_stream()
        self.stream.start()
        self.last_mention = None
        self.screen_name = 'pypoet'
        self.seen_users = set()

    def load_twitter(self):
        return Twitter(auth=self.auth, api_version='1.1')

    def load_stream(self):
        return StreamHandler(auth=self.auth)

    def fetch_posts(self, user_name, count=200):
        max_items = 200
        tweets = list()

        params = {'screen_name': user_name,
                  'trim_user': 1, 'count': min(max_items, count)}
        # we get an array of length 1 when we're out of entries
        posts = [None, None]
        while len(posts) > 1:
            posts = self.api.statuses.user_timeline(**params)
            next_id = min([int(p.get('id_str')) for p in posts])
            params['max_id'] = next_id
            tweets.extend(posts)
        return tweets

    def manual_fetch_new_mentions(self):
        params = {'count': 200}
        if self.last_mention:
            params['since_id'] = self.last_mention
        mentions = self.api.statuses.mentions_timeline(**params)
        if len(mentions):
            self.last_mention = max(int(m.get('id_str')) for m in mentions)
        users = [m.get('entities').get('user_mentions') for m in mentions]
        users = [m for m in users if len(m)]
        print(users)

    def new_user_events(self):
        """fetch new items in the user stream"""
        events = list()
        while True:
            event = self.stream.next()
            if event not None:
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
        """ handle mentions etc """
        events = new_user_events()
        if len(events):
            # handle mentions
            mentions = [
                e for e in events if e.get('entities', dict()).get('user_mentions')]
            mentions = [prune_mention(e) for e in mentions]
            mentions = [m for m in mentions if self.screen_name in m.get(mentions)]
            users = set([m.get('user').get('screen_name') for m in mentions])
            users = users.difference(self.seen_users)
            self.seen_users.update(users)
            userstweets = [(u, self.fetch_posts(u)) for u in users]
            return userstweets



def main():
    t = TwitterHandler()
    for i in t.stream:
        print(i)

    # return fetch_posts('cmyr')
    # import argparse
    # parser = argparse.ArgumentParser()
    # parser.add_argument('-o', '--outpath', type=str, default=output_url, help="set outpath")
    # parser.add_argument('-c', '--count', type=int, default=20, help='number of items to save')
    # args = parser.parse_args()
    # fetch_recent_posts(**vars(args))


if __name__ == "__main__":
    main()
