# coding: utf-8
from __future__ import print_function
from __future__ import unicode_literals

import functools

import zmqstream

from zmqstream.publisher import (StreamPublisher, StreamResult, StreamResultItem)
import twittertools
import poetryutils2 as poetry
from saver import save_poem

""" cleans up stream results and rebroadcasts them """


def tweet_filter(source_iter, langs=['en']):
    langs = set(langs)
    for item in source_iter:
        if item.get('retweeted_status'):
            continue
        if item.get('lang') not in langs:
            continue
        if item.get('text'):
            yield stripped_tweet(item)


def stripped_tweet(tweet):
    dict_template = {"text": True, "id_str": True, 'lang': True,
                     "user": {"screen_name": True, "name": True, 'profile_image_url': True}}
    return twittertools.prune_dict(tweet, dict_template)


def line_iter(host="127.0.0.1", port="8069", request_kwargs=None, save=False):
    poet = poetry.sorting.MultiPoet(poets=[
        poetry.sorting.Haikuer(lang='fr'),
        poetry.sorting.Limericker(),
        ])

    stream = tweet_filter(
        zmqstream.zmq_iter(host=host, port=port),
        langs=['en', 'fr'])

    line_filters = [
        poetry.filters.numeral_filter,
        poetry.filters.url_filter,
        poetry.filters.hashtag_filter,
        poetry.filters.screenname_filter,
        poetry.filters.low_letter_filter(0.75),
        poetry.filters.bad_swears_filter(),
        poetry.filters.emoji_filter
    ]

    lang_filters = {
        'en': [
            poetry.filters.real_word_ratio_filter(0.8, lang='en')],
        'fr': [
            poetry.filters.real_word_ratio_filter(0.8, lang='fr'),
            poetry.filters.bad_swears_filter('fr')]
        }

    for line in poetry.line_iter(stream, line_filters, key='text'):
        if (line.get("lang") not in ('en', 'fr') or not
                all(f(poetry.utils.unicodify(line['text'])) for f in lang_filters[line['lang']])):
            continue

        poem = poet.add_keyed_line(line, key='text')

        if not isinstance(poem, list):
            poem = [poem]
        for p in poem:
            if isinstance(p, poetry.sorting.Poem):
                if save:
                    save_poem(p)
                yield StreamResult(StreamResultItem, {'poem': p.to_dict()})


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--hostin', type=str, help="source host")
    parser.add_argument('--portin', type=str, help="source port")
    parser.add_argument('--hostout', type=str, help="host out")
    parser.add_argument('--portout', type=str, help="port out")
    args = parser.parse_args()

    source_host = args.hostin or '127.0.0.1'
    source_port = args.portin or 8069
    dest_host = args.hostout or '127.0.0.1'
    dest_port = args.portout or 8070

    iterator = functools.partial(line_iter, source_host, source_port)
    publisher = StreamPublisher(
        iterator=iterator,
        hostname=dest_host,
        port=dest_port)
    publisher.run()


if __name__ == "__main__":
    main()
