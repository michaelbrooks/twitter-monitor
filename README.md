Twitter Monitor
===============

[![Build Status](https://travis-ci.org/michaelbrooks/twitter-monitor.png?branch=master)](https://travis-ci.org/michaelbrooks/twitter-monitor)
[![Coverage Status](https://coveralls.io/repos/michaelbrooks/twitter-monitor/badge.png)](https://coveralls.io/r/michaelbrooks/twitter-monitor)

A Twitter streaming library built on [Tweepy](https://github.com/tweepy/tweepy) that enables dynamic tracking
of the [filtered Twitter Streaming API](https://dev.twitter.com/docs/api/1.1/post/statuses/filter).

This library provides a framework that you can use to build your own dynamic Twitter term tracking system.
You will want to do three things:

1. Create a subclass of `TermChecker` that knows how to look for tracked terms (e.g. in a database or a file).
   There is a `FileTermChecker` provided as an example.
2. Create a subclass of `JsonStreamListener` that does something interesting with the tweets. Maybe write tweets
   to a file a database.
3. Start an instance of the `DynamicTwitterStream` class, which ties it all together.


####Installation

```bash
$ pip install twitter-monitor
```


Example Usage
-------------

Below is a simple example of how to set up and initialize a dynamic Twitter stream.
This example uses the `FileTermChecker` and default `JsonStreamListener` implementations:

```python
import tweepy
import twitter_monitor

# The file containing terms to track
terms_filename = "tracking_terms.txt"

# How often to check the file for new terms
poll_interval = 15

# Your twitter API credentials
api_key = 'YOUR API KEY'
api_secret = 'YOUR API SECRET'
access_token = 'YOUR ACCESS TOKEN'
access_token_secret = 'YOUR ACCESS TOKEN SECRET'

auth = tweepy.OAuthHandler(api_key, api_secret)
auth.set_access_token(access_token, access_token_secret)

# Construct your own subclasses here instead
listener = twitter_monitor.JsonStreamListener()
checker = twitter_monitor.FileTermChecker(filename=terms_filename)

# Start and maintain the streaming connection...
stream = twitter_monitor.DynamicTwitterStream(auth, listener, checker)
while True:
    try:
        # Loop and keep reconnecting in case something goes wrong
        # Note: You may annoy Twitter if you reconnect too often under some conditions.
        stream.start(poll_interval)
    except Exception as e:
        print e
        time.sleep(1)  # to avoid craziness with Twitter
```


Checking for Terms
------------------

To create a custom `TermChecker`, you need to override the `update_tracking_terms(self)` method.
This method must return a *set* of terms. `update_tracking_terms()` will be called
on your checker periodically to refresh the term list.

The `twitter_monitor.checker.FileTermChecker` class is included as an example.


Handling Tweets
---------------

The Twitter streaming API emits various types of messages.
The `JsonStreamListener` class includes stub methods for handling each of these.
Please refer to the [documentation](https://dev.twitter.com/docs/streaming-apis/messages) for more information
about what these messages mean.

Create a subclass of `JsonStreamListener`, overriding the handler methods for any message types you wish to respond to.
Here is a simple Listener that just prints out tweets:

```python
import twitter_monitor
import json

class PrintingListener(twitter_monitor.JsonStreamListener):

    def on_status(self, status):
        print json.dumps(status, indent=3)

    def on_limit(self, track):
        print "Horrors, we lost %d tweets!" % track
```

Note that the `on_exception()` handler is a bit different. It is called when there is some exception
from within the tweepy streaming thread. By default the exception will be stored in the `stream_exception` field
on your listener object.

More info about how listeners are used may be gleaned from the
[Tweepy source code](https://github.com/tweepy/tweepy/blob/master/tweepy/streaming.py#L22).


Questions and Contributing
--------------------------

Feel free to post questions and problems on the issue tracker. Pull requests welcome!

