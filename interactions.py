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
from twitter.api import Twitter, TwitterError, TwitterHTTPError
from twitter.stream import TwitterStream, Timeout, HeartbeatTimeout, Hangup
from twitter.oauth import OAuth

from twittercreds import (CONSUMER_KEY, CONSUMER_SECRET, ACCESS_KEY, ACCESS_SECRET)

class TwitterHandler(object):
    """wraps twitter API calls and tracks related state"""
    def __init__(self):
        super(TwitterHandler, self).__init__()
        self.auth = OAuth(ACCESS_KEY, ACCESS_SECRET, CONSUMER_KEY, CONSUMER_SECRET)
        self.api = self.load_twitter()     
        self.stream = self.load_stream()
        self.last_mention = None
    
    def load_twitter(self):
        return Twitter(auth=self.auth, api_version='1.1')

    def load_stream(self):
        return TwitterStream(auth=self.auth, 
            domain='userstream.twitter.com').user(replies='all', with='user')


    def fetch_posts(self, user_name, count=200):
        max_items = 200
        tweets = list()

        params = {'screen_name': user_name, 'trim_user': 1, 'count': min(max_items, count)}
        posts = [None, None] # we get an array of length 1 when we're out of entries
        while len(posts) > 1:
            posts = self.api.statuses.user_timeline(**params)
            next_id = min([int(p.get('id_str')) for p in posts])
            params['max_id'] = next_id
            tweets.extend(posts)
        for t in [p.get('text') for p in tweets]:
            print(t)

    def new_mentions(self):
        params = {'count': 200}
        if self.last_mention:
            params['since_id'] = self.last_mention
        mentions = self.api.statuses.mentions_timeline(**params)
        if len(mentions):
            self.last_mention = max(int(m.get('id_str')) for m in mentions)
        users = [m.get('entities').get('user_mentions') for m in mentions]
        users = [m for m in users if len(m)]
        print(users)




def main():
    pass
    # return fetch_posts('cmyr')
    # import argparse
    # parser = argparse.ArgumentParser()
    # parser.add_argument('-o', '--outpath', type=str, default=output_url, help="set outpath")
    # parser.add_argument('-c', '--count', type=int, default=20, help='number of items to save')
    # args = parser.parse_args()
    # fetch_recent_posts(**vars(args))




if __name__ == "__main__":
    main()