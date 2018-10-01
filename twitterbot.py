#!/usr/bin/python

from twython import Twython, TwythonError, TwythonStreamer
import sys
import signal
from datetime import datetime, date, time

import logging
import logging.handlers

from Queue import Queue
from threading import Thread

LOG_FILENAME = '/var/log/twitterstream/twitterstream-'+datetime.now().strftime("%d:%b:%Y")+'.log'

# Set up a specific logger with our desired output level
my_logger = logging.getLogger(__name__)
my_logger.setLevel(logging.INFO)

# Create handler
handler = logging.FileHandler(LOG_FILENAME)
handler.setLevel(logging.INFO)
# create formatter
formatter = logging.Formatter("%(asctime)s-%(name)s-%(levelname)s-%(message)s", "%Y-%m-%d %H:%M:%S")
# add formatter to handler
handler.setFormatter(formatter)

# Add the log message handler to the logger
my_logger.addHandler(handler)

# The keys for this app
APP_KEY = ''
APP_SECRET = ''

# The keys generated by the authorisation of 'NoToHullTigers' 
OAUTH_TOKEN = ''
OAUTH_TOKEN_SECRET = ''

class MyStreamer(TwythonStreamer):
	def on_success(self, data):
		my_logger.debug(data)
		if 'text' in data:
			tweet = data['text'].encode('utf-8')
			user_name = data['user']['screen_name'].encode('utf-8')
			my_logger.debug(user_name)
			my_logger.debug(tweet)
			if ('hull city tigers' in tweet.lower()) or ('hull tigers' in tweet.lower()):
				my_logger.info("@"+user_name+": "+tweet)
				i = data['id_str']
				r = "@"+user_name+" #NoToHullTigers "
				tweet_queue.put({'r': r, 'i': i})
				my_logger.info("Queue length: "+str(tweet_queue.qsize()))
			if not tweet_thread.isAlive():
				my_logger.error("worker thread has died")
		return True

	def on_error(self, status_code, data):
		my_logger.error("Streamer Error. Disconnecting")
		self.disconnect()
		
	def on_timeout(self):
		my_logger.error("Timeout. Disconnecting")
		self.disconnect()


# Requires Authentication as of Twitter API v1.1

#twitter = Twython(APP_KEY, APP_SECRET)
#auth = twitter.get_authentication_tokens()
#OAUTH_TOKEN = auth['oauth_token']
#OAUTH_TOKEN_SECRET = auth['oauth_token_secret']
#print 'Go to URL '+auth['auth_url']+' and get authorisation PIN'

#pin = raw_input("Enter PIN: ")
#twitter = Twython(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
#final_step = twitter.get_authorized_tokens(pin)

#OAUTH_TOKEN = final_step['oauth_token']
#OAUTH_TOKEN_SECRET = final_step['oauth_token_secret']

#pp.pprint(final_step)

my_logger.info("Starting")

tweet_queue = Queue()

stream = MyStreamer(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)

def worker():
    twitter = Twython(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
    while True:
        item = tweet_queue.get()
	my_logger.info(item['r'])
	try:
		twitter.update_status(status=item['r'], in_reply_to_status_id=item['i'] )
	except TwythonError:
		my_logger.exception("Twitter Update Error: "+item['r'])
#	except:
#		my_logger.exception("Unexpected error: "+item['r'])
        tweet_queue.task_done()

tweet_thread = Thread(target=worker)
tweet_thread.start()

def int_handler(signum, frame):
    stream.disconnect()
    my_logger.info("Exiting")
    sys.exit(0)

signal.signal(signal.SIGTERM, int_handler)
signal.signal(signal.SIGINT, int_handler)

stream.statuses.filter(track='Hull Tigers')

