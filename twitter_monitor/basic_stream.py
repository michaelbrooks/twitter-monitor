"""
A simple streaming helper that takes
minimal configuration as arguments and starts
a stream to stdout.
"""

import signal
import logging
import time
import json

import tweepy
from listener import JsonStreamListener
from checker import FileTermChecker
from stream import DynamicTwitterStream

logger = logging.getLogger(__name__)

class PrintingListener(JsonStreamListener):
    def __init__(self, api=None, out=None):
        super(PrintingListener, self).__init__(api)
        if out is None:
            import sys
            out = sys.stdout

        self.out = out
        self.terminate = False
        self.received = 0
        self.since = time.time()

    def on_status(self, status):
        self.out.write(json.dumps(status))
        self.received += 1
        return not self.terminate

    def set_terminate(self):
        """Notify the tweepy stream that it should quit"""
        self.terminate = True

    def print_status(self):
        """Print out the current tweet rate and reset the counter"""
        tweets = self.received
        now = time.time()
        diff = now - self.since
        self.since = now
        self.received = 0
        if diff > 0:
            logger.info("Receiving tweets at %s tps", tweets / diff)


class BasicFileTermChecker(FileTermChecker):
    """Modified to print out status periodically"""

    def __init__(self, filename, listener):
        super(BasicFileTermChecker, self).__init__(filename)
        self.listener = listener

    def update_tracking_terms(self):
        self.listener.print_status()
        return super(BasicFileTermChecker, self).update_tracking_terms()


def debugger(sig, frame):
    """
    Interrupt running process, and provide a python prompt for
    interactive debugging.
    """
    d={'_frame':frame}         # Allow access to frame object.
    d.update(frame.f_globals)  # Unless shadowed by global
    d.update(frame.f_locals)

    import code, traceback
    i = code.InteractiveConsole(d)
    message  = "Signal received : entering python shell.\nTraceback:\n"
    message += ''.join(traceback.format_stack(frame))
    i.interact(message)


def start(track_file,
          twitter_api_key,
          twitter_api_secret,
          twitter_access_token,
          twitter_access_token_secret,
          poll_interval=15,
          unfiltered=False,
          languages=None,
          debug=False):

    # Make a tweepy auth object
    auth = tweepy.OAuthHandler(twitter_api_key, twitter_api_secret)
    auth.set_access_token(twitter_access_token, twitter_access_token_secret)

    listener = PrintingListener()
    checker = BasicFileTermChecker(track_file, listener)

    # Make sure the terms file is ok
    if not unfiltered and not checker.update_tracking_terms():
        logger.error("No terms in track file %s", checker.filename)
        exit(1)

    logger.info("Monitoring track file %s", track_file)

    def stop(signum, frame):
        """
        Exit cleanly.
        """
        logger.info("Stopping because of signal")

        # Let the tweet listener know it should be quitting asap
        listener.set_terminate()

        raise SystemExit()

    # Installs signal handlers for handling SIGINT and SIGTERM
    # gracefully.
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    
    if debug:
        signal.signal(signal.SIGUSR1, debugger)

    # Start and maintain the streaming connection...
    stream = DynamicTwitterStream(auth, listener, checker, unfiltered=unfiltered, languages=languages)
    while True:
        try:
            stream.start_polling(poll_interval)
        except Exception as e:
            logger.error("Exception while polling", exc_info=True)
            time.sleep(1)  # to avoid craziness
