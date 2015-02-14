Twitter Monitor
===============

[![Build Status](https://travis-ci.org/michaelbrooks/twitter-monitor.svg?branch=master)](https://travis-ci.org/michaelbrooks/twitter-monitor)
[![Coverage Status](https://coveralls.io/repos/michaelbrooks/twitter-monitor/badge.svg?branch=master)](https://coveralls.io/r/michaelbrooks/twitter-monitor?branch=master)

A Twitter streaming library built on [Tweepy](https://github.com/tweepy/tweepy) that enables dynamic tracking
of the [filtered Twitter Streaming API](https://dev.twitter.com/docs/api/1.1/post/statuses/filter).

This library provides a framework that you can use to build your own dynamic Twitter term tracking system.
You will want to do three things:

1. Create a subclass of `TermChecker` that knows how to look for tracked terms (e.g. in a database or a file).
   There is a `FileTermChecker` provided as an example.
2. Create a subclass of `JsonStreamListener` that does something interesting with the tweets. Maybe write tweets
   to a file a database.
3. Start an instance of the `DynamicTwitterStream` class, which ties it all together.

There is also a `stream_tweets` script you can use to get started
streaming tweets more quickly. More information is [below](#streaming-script).


####Installation

This package is available on PyPI [here](https://pypi.python.org/pypi/twitter-monitor).

```bash
$ pip install twitter-monitor
```


### Simple Streaming Script

This package includes a `stream_tweets` script that
connects to Twitter using your API key, reads
a list of filter terms from a file, and streams
tweets to stdout.

To use `stream_tweets`, you will need to create a file
containing your filter terms, one per line.
The script will look for `track.txt` in the current directory,
but you can override this.
You also need to provide your Twitter API key info.

By default, an empty tracking file will result in no tweets
being captured. If you want to instead capture unfiltered tweets
using the `sample` API endpoint, you can use the "unfiltered" options
(details below).

When you run `stream_tweets`, informational messages will be
printed out to stderr, while tweets will be printed to stdout,
one tweet per line, in JSON format.
This makes it convenient to redirect the output into a file or another program:

```bash
$ stream_tweets > tweets.json
```

The required settings can be provided via environment variables,
a `.ini` file, or command-line arguments.
The command-line arguments take precedent:

```bash
$ stream_tweets --api-key XXXX --api-secret XXXX \
                --access-token XXXX --access-token-secret XXXX \
                --track-file my/track/file.txt \
                --poll-interval 15
```

The `--poll-interval` option defines how often to check the track file
for updated terms. You can also use the option `--unfiltered TRUE` to
enable capturing tweets without terms.

Alternatively, one or more of the options may be defined in a `.ini` file.
The script will search in the current directory for `twitter_monitor.ini`, but this can be overridden
using the `--ini-file` argument.
Below is an example `twitter_monitor.ini`:

```ini
[twitter]
api_key=XXXX
api_secret=XXXX
access_token=XXXX
access_token_secret=XXXX
track_file=my/track/file.txt
poll_interval=15
unfiltered=TRUE
```

If options are not defined on the command line or in an ini file,
environment variables are checked. Below are the names of the corresponding
environment variables:

```bash
TWITTER_API_KEY=XXXX
TWITTER_API_SECRET=XXXX
TWITTER_ACCESS_TOKEN=XXXX
TWITTER_ACCESS_TOKEN_SECRET=XXXX
TWITTER_TRACK_FILE=my/track/file.txt
TWITTER_POLL_INTERVAL=15
TWITTER_UNFILTERED=TRUE
```

Custom Usage
-------------

Below is a simple example of how to set up and initialize a dynamic Twitter stream.
This example uses the `FileTermChecker` and default `JsonStreamListener` implementations.
There is a working example in the `twitter_monitor/basic_stream.py` file.

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


### Checking for Terms

To create a custom `TermChecker`, you need to override the `update_tracking_terms(self)` method.
This method must return a *set* of terms. `update_tracking_terms()` will be called
on your checker periodically to refresh the term list.

The `twitter_monitor.checker.FileTermChecker` class is included as an example.

If you are not using filter terms, construct your DynamicTwitterStream
object with the `unfiltered` keyword argument set to True.

### Handling Tweets

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

Use `python setup.py test` to run tests.


### Creating a release

1. Increment the version number in `setup.py`. Commit and push.
2. Create a new Release in GitHub with the appropriate version tag.
3. Run `setup.py sdist bdist` to build the distribution for PyPi.
4. Run `twine upload -u USERNAME -p PASSWORD dist/*` to upload to PyPi. 
   You must have [twine](https://github.com/pypa/twine) installed.
