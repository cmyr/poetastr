# coding: utf-8
from __future__ import print_function
from __future__ import unicode_literals

import functools
from collections import deque
import time

from twitter.oauth import OAuth

import zmqstream
from zmqstream.publisher import (StreamPublisher, StreamResult,
                                 StreamResultError, StreamResultItem)
import twittertools
import poetryutils2 as poetry
import interactions
from itercombiner import IterCombiner
from saver import save_poem

""" cleans up stream results and rebroadcasts them """


def tweet_filter(source_iter):
    for item in source_iter:
        if item.get('retweeted_status'):
            continue
        if item.get('lang') != 'en':
            continue
        if item.get('text'):
            yield stripped_tweet(item)


def stripped_tweet(tweet):
    dict_template = {"text": True, "id_str": True,
                     "user": {"screen_name": True, "name": True}}
    return twittertools.prune_dict(tweet, dict_template)


def iter_wrapper(source_iter, key=None):
    """ 
    wraps an iterator and displays a graphic activity indicator
    so you don't have to look at a blank console and hope things are running.
    """
    activity_indicator = zmqstream.ActivityIndicator()
    count = 0
    for i in source_iter:
        count += 1
        if not key:
            last_word = i.split()[-1]
        else:
            last_word = i.get(key).split()[-1]
        yield i


def line_iter(user_auth, host="127.0.0.1", port="8069", request_kwargs=None):
    poets = [poetry.sorting.Limericker(), poetry.sorting.Haikuer()]
    poet = poetry.sorting.MultiPoet(poets=poets)

    stream = tweet_filter(zmqstream.zmq_iter(host=host, port=port))
    twitter = interactions.TwitterHandler(auth=user_auth)

    line_filters = [
        poetry.filters.numeral_filter,
        poetry.filters.ascii_filter,
        poetry.filters.url_filter,
        poetry.filters.real_word_ratio_filter(0.8),
        poetry.filters.hashtag_filter,
        poetry.filters.screenname_filter,
        poetry.filters.low_letter_filter(0.8),
        poetry.filters.bad_swears_filter()
    ]

    itercombiner = IterCombiner(
        poetry.line_iter(stream, line_filters, key='text'))
    for line in itercombiner:
        poem = poet.add_keyed_line(line, key='text')
        if line.get('special_user'):
            yield StreamResult(StreamResultItem, {'user-line': line})
        else:
            yield StreamResult(StreamResultItem, {'line': line.get('text')})

        if isinstance(poem, list):
            for p in poem:
                save_poem(p)
                yield StreamResult(StreamResultItem, {'poem': p.to_dict()})
        elif isinstance(poem, poetry.sorting.Poem):
            save_poem(poem)
            yield StreamResult(StreamResultItem, {'poem': poem.to_dict()})

        # handle user mentions:
        usertweets = twitter.userstweets
        if usertweets:
            print('found user')
            for user, tweets in usertweets:
                filtered_tweets = [t for t in tweet_filter(tweets) if t]
                filtered_tweets = [t for t in
                    poetry.line_iter(filtered_tweets, line_filters, key='text')]
                payload = {
                    'screen_name': user,
                    'total_count': len(tweets),
                    'filtered_count': len(filtered_tweets)}
                yield StreamResult(StreamResultItem, {'track-user': payload})
                for t in filtered_tweets:
                    t['special_user'] = user
                itercombiner.add_items(filtered_tweets)
        else:
            rate_limit = twitter.process_user_events()
            if rate_limit:
                yield StreamResult(StreamResultItem, {'rate-limit': {'wait_time': rate_limit}})
        


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('auth', type=str, help="path to twitter auth token")
    parser.add_argument('--hostin', type=str, help="source host")
    parser.add_argument('--portin', type=str, help="source port")
    parser.add_argument('--hostout', type=str, help="host out")
    parser.add_argument('--portout', type=str, help="port out")
    args = parser.parse_args()

    source_host = args.hostin or '127.0.0.1'
    source_port = args.portin or 8069
    dest_host = args.hostout or '127.0.0.1'
    dest_port = args.portout or 8070

    creds = twittertools.load_auth(args.auth, raw=True)
    # the OAuth object in the twitter module has different positional arguments
# then the requests OAuth module used in my own streaming implementation
    auth = OAuth(creds[2], creds[3], creds[0], creds[1])

    iterator = functools.partial(line_iter, auth, source_host, source_port)
    for line in iterator():
        print(line)
    publisher = StreamPublisher(
        iterator=iterator,
        hostname=dest_host,
        port=dest_port)
    publisher.run()


if __name__ == "__main__":
    main()
