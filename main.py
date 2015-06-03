
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

app = Flask(__name__)

def encode_message(message_type, body):
    jsonable = {'mtype': message_type, 'body': body}
    return 'data: %s\n\n' % json.dumps(jsonable)


EXPECTED_KEYS = set(['line', 'user-line', 'poem', 'track-user', 'rate-limit'])

def poet_sse_iter(host="127.0.0.1", port="8070", debug=False, remote=True):
    """
    connects to the zmq feeder and turns results into server-sent-events
    """
    kwargs = {}
    if remote:
        kwargs = {'tunnel': 'pcmyr@h.cmyr.net:51415'}
    iterator = zmqstream.zmq_iter(host, port, **kwargs)
    for item in iterator:
        assert(len(item) == 1), item
        key, payload = item.items()[0]
        assert(key in EXPECTED_KEYS)
        # assert(isinstance(payload, dict)), payload
        yield encode_message(key, payload)


@app.route('/my_event_source')
def sse_request():
    return Response(
    #    poem_source('192.168.1.103'),
        poet_sse_iter(),
        mimetype='text/event-stream')


@app.route('/')
def page():
    return render_template('index.html')

if __name__ == '__main__':
    # for line in poem_source('192.168.1.103'):
    # for line in poet_sse_iter():
    #     print("%s %s" % (line.get('mtype'), line.get('body', line)))
    # print('hi')
    http_server = WSGIServer(('127.0.0.1', 8001), app)
    http_server.serve_forever()
