# coding: utf-8

from __future__ import print_function
from __future__ import unicode_literals

import os

import json
import gevent
import gevent.monkey
from gevent.pywsgi import WSGIServer

from flask import Flask, Response, render_template

import zmqstream

gevent.monkey.patch_all()
app = Flask(__name__)

TUNNEL = None


def encode_message(message_type, body):
    jsonable = {'mtype': message_type, 'body': body}
    return 'data: %s\n\n' % json.dumps(jsonable)

EXPECTED_KEYS = set(['line', 'user-line', 'poem', 'track-user', 'rate-limit', 'keep_alive'])


def poet_sse_iter(host="127.0.0.1", port="8070", debug=False):
    """
    connects to the zmq feeder and turns results into server-sent-events
    """
    kwargs = {}
    if TUNNEL:
        kwargs = {'tunnel': TUNNEL}
    iterator = zmqstream.zmq_iter(host, port, **kwargs)
    for item in iterator:
        assert(len(item) == 1), item
        key, payload = item.items()[0]
        assert(key in EXPECTED_KEYS)
        yield encode_message(key, payload)
        gevent.sleep(0.05)


@app.route('/my_event_source')
def sse_request():
    return Response(
        poet_sse_iter(),
        mimetype='text/event-stream')


@app.route('/')
def page():
    return render_template('index.html')


@app.route('/client_wrote_poem')
def client_callback():
    '''
    added for installation purposes: touch a file when the client displays a result
    I have a seperate cron job that checks the mod date on this file and notifies me if
    something goes wrong
    '''
    print('callback hit')
    with open(os.path.expanduser('~/.poetastr-callback'), 'w') as f:
        f.write(':)')
    return 'True'


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tunnel', type=str, help="sever for tunneling over ssh")
    args = parser.parse_args()
    if args.tunnel:
        global TUNNEL
        TUNNEL = args.tunnel

    http_server = WSGIServer(('127.0.0.1', 8001), app)
    http_server.serve_forever()


if __name__ == '__main__':
    main()
