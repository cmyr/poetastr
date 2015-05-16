
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
    # if re.search(r'\n\n', text):
    #     print('bad message: %s' % text)
    # text = re.sub(r'\n+', r'\n', text)
    jsonable = {'mtype': message_type, 'body': body}
    return 'data: %s\n\n' % json.dumps(jsonable)
    # return 'data: {"mtype": "%s", "text": "%s"}\n\n' % (message_type, text)

def tweet_filter(source_iter):
    for item in source_iter:
        if item.get('retweeted_status'):
            continue
        if item.get('lang') != 'en':
            continue
        if item.get('text'):
            yield stripped_tweet(item)


def stripped_tweet(tweet):
    dict_template = {"text": True, "id_str": True, "user": {"screen_name": True, "name": True}}
    return twittertools.prune_dict(tweet, dict_template)

def iter_wrapper(source_iter, key=None):
    activity_indicator = zmqstream.ActivityIndicator()
    count = 0
    for i in source_iter:
        count += 1
        if not key:
            last_word = i.split()[-1]
        else:
            last_word = i.get(key).split()[-1]
        # activity_indicator.message = last_word + " %d" % count
        # activity_indicator.tick()
        yield i

def poem_source(host="127.0.0.1", port="8069", debug=False):
    poet = poetry.Haikuer()
    tweet_texts = tweet_filter(zmqstream.zmq_iter(host=host, port=port))
    # tweet_texts = open(os.path.expanduser('~/tweetdbm/may04.txt')).readlines()

    line_filters = [
    poetry.filters.numeral_filter,
    poetry.filters.ascii_filter,
    poetry.filters.url_filter,
    poetry.filters.real_word_ratio_filter(0.9)
    ]

    source = poetry.line_iter(tweet_texts, line_filters, key='text')
    for item in poet.generate_from_source(iter_wrapper(source, key='text'), key='text', yield_lines=True):
        # print(poet.prettify(poem))
        if isinstance(item, basestring):
            yield encode_message('line', item)
        elif isinstance(item, tuple):
            yield encode_message('poem', poet.dictify(item))


# def event_stream():
#     count = 0
#     while True:
#         gevent.sleep(2)
#         payload_str = 'count: %s' % count
#         yield encode_message('count', payload_str)
#         if count % 3 == 0:
#             yield encode_message('item', 'three #%d' % int(count/3))
#         count += 1

@app.route('/my_event_source')
def sse_request():
    return Response(
            poem_source('192.168.1.103'),
            mimetype='text/event-stream')

@app.route('/')
def page():
    return render_template('sse.html')

if __name__ == '__main__':
    # for line in poem_source('192.168.1.103'):
    #     print(line)
    http_server = WSGIServer(('127.0.0.1', 8001), app)
    http_server.serve_forever()


# # author: oskar.blom@gmail.com
# #
# # Make sure your gevent version is >= 1.0
# import gevent
# from gevent.wsgi import WSGIServer
# from gevent.queue import Queue

# from flask import Flask, Response

# import time


# # SSE "protocol" is described here: http://mzl.la/UPFyxY
# class ServerSentEvent(object):

#     def __init__(self, data):
#         self.data = data
#         self.event = None
#         self.id = None
#         self.desc_map = {
#             self.data : "data",
#             self.event : "event",
#             self.id : "id"
#         }

#     def encode(self):
#         if not self.data:
#             return ""
#         lines = ["%s: %s" % (v, k) 
#                  for k, v in self.desc_map.iteritems() if k]
        
#         return "%s\n\n" % "\n".join(lines)

# app = Flask(__name__)
# subscriptions = []

# # Client code consumes like this.
# @app.route("/")
# def index():
#     debug_template = """
#      <html>
#        <head>
#        </head>
#        <body>
#          <h1>Server sent events</h1>
#          <div id="event"></div>
#          <script type="text/javascript">

#          var eventOutputContainer = document.getElementById("event");
#          var evtSrc = new EventSource("/subscribe");

#          evtSrc.onmessage = function(e) {
#              console.log(e.data);
#              eventOutputContainer.innerHTML = e.data;
#          };

#          </script>
#        </body>
#      </html>
#     """
#     return(debug_template)

# @app.route("/debug")
# def debug():
#     return "Currently %d subscriptions" % len(subscriptions)

# @app.route("/publish")
# def publish():
#     #Dummy data - pick up from request for real data
#     def notify():
#         msg = str(time.time())
#         for sub in subscriptions[:]:
#             sub.put(msg)
    
#     gevent.spawn(notify)
    
#     return "OK"

# @app.route("/subscribe")
# def subscribe():
#     def gen():
#         q = Queue()
#         subscriptions.append(q)
#         try:
#             while True:
#                 result = q.get()
#                 ev = ServerSentEvent(str(result))
#                 yield ev.encode()
#         except GeneratorExit: # Or maybe use flask signals
#             subscriptions.remove(q)

#     return Response(gen(), mimetype="text/event-stream")

# if __name__ == "__main__":
#     app.debug = True
#     server = WSGIServer(("", 5000), app)
#     server.serve_forever()
#     # Then visit http://localhost:5000 to subscribe 

#     # and send messages by visiting http://localhost:5000/publish