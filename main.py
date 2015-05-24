
import re
import json
import gevent
import gevent.monkey
from gevent.pywsgi import WSGIServer
gevent.monkey.patch_all()

from flask import Flask, request, Response, render_template

import poetryutils2 as poetry
import twittertools
import zmqstream
import interactions

app = Flask(__name__)
twitter = interactions.TwitterHandler()


def encode_message(message_type, body):
    jsonable = {'mtype': message_type, 'body': body}
    return 'data: %s\n\n' % json.dumps(jsonable)


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


def line_iter(host="127.0.0.1", port="8069"):
    stream = tweet_filter(zmqstream.zmq_iter(host=host, port=port))

    line_filters = [
        poetry.filters.numeral_filter,
        poetry.filters.ascii_filter,
        poetry.filters.url_filter,
        poetry.filters.real_word_ratio_filter(0.9)
    ]

    return poetry.line_iter(stream, line_filters, key='text')


def poem_source(host="127.0.0.1", port="8069", debug=False):
    # poet = poetry.Concrete()
    poets = [poetry.sorting.Limericker(), poetry.sorting.Haikuer()]
    poet = poetry.sorting.MultiPoet(poets=poets)
    stream = line_iter(host, port)

    for line in stream:
        poem = poet.add_keyed_line(line, key='text')
        has_poem = poem != None
        # yield encode_message('line', {'line': line, 'has_poem': has_poem})
        yield encode_message('line', line.get('text'))

        if isinstance(poem, list):
            for p in poem:
                yield encode_message('poem', p.to_dict())
        elif isinstance(poem, poetry.sorting.Poem):
            yield encode_message('poem', poem.to_dict())
        
        elif not poem:
            # process user events
            user_lines = twitter.process_user_events()
            for user, tweets in user_lines:
                tweets = [stripped_tweet(t) for t in tweets]
                filtered = poetry.lines(tweets, line_filters, key='text')
                yield encode_message(
                    'user',
                    {'total_count': len(tweets),
                     'filtered_count': len(filtered)})
                for line in filtered:
                    line['special'] = True
                    poem = poet.add_keyed_line(line, key='text')
                    if isinstance(poem, list):
                        for p in poem:
                            yield encode_message('poem', p.to_dict())
                    elif isinstance(poem, poetry.sorting.Poem):
                        yield encode_message('poem', poem.to_dict())


@app.route('/my_event_source')
def sse_request():
    return Response(
        poem_source('192.168.1.103'),
        # poem_source(),
        mimetype='text/event-stream')


@app.route('/')
def page():
    return render_template('index.html')

if __name__ == '__main__':
    # for line in poem_source('192.168.1.103'):
    # for line in poem_source():
    #     print(line)
    # print('hi')
    http_server = WSGIServer(('127.0.0.1', 8001), app)
    http_server.serve_forever()
