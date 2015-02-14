"""
A simple streaming helper that takes
minimal configuration as arguments and starts
a stream to stdout.
"""

import os
import signal
import logging
import time
import json

import tweepy
from listener import JsonStreamListener
from checker import FileTermChecker
from stream import DynamicTwitterStream

logger = logging.getLogger(__name__)

__all__ = ['start']


class PrintingListener(JsonStreamListener):
    """A listener that writes to a file or stdout"""

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
        """Print out some tweets"""
        self.out.write(json.dumps(status))
        self.out.write(os.linesep)

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
        logger.info("Monitoring track file %s", filename)
        super(BasicFileTermChecker, self).__init__(filename)
        self.listener = listener


    def update_tracking_terms(self):
        self.listener.print_status()
        return super(BasicFileTermChecker, self).update_tracking_terms()


def launch_debugger(frame, stream=None):
    """
    Interrupt running process, and provide a python prompt for
    interactive debugging.
    """

    d = {'_frame': frame}  # Allow access to frame object.
    d.update(frame.f_globals)  # Unless shadowed by global
    d.update(frame.f_locals)

    import code, traceback

    i = code.InteractiveConsole(d)
    message = "Signal received : entering python shell.\nTraceback:\n"
    message += ''.join(traceback.format_stack(frame))
    i.interact(message)


def set_debug_listener(stream):
    """Break into a debugger if receives the SIGUSR1 signal"""

    def debugger(sig, frame):
        launch_debugger(frame, stream)

    if hasattr(signal, 'SIGUSR1'):
        signal.signal(signal.SIGUSR1, debugger)
    else:
        logger.warn("Cannot set SIGUSR1 signal for debug mode.")

def terminate(listener):
    """
    Exit cleanly.
    """
    logger.info("Stopping because of signal")

    # Let the tweet listener know it should be quitting asap
    listener.set_terminate()

    raise SystemExit()

def set_terminate_listeners(stream):
    """Die on SIGTERM or SIGINT"""

    def stop(signum, frame):
        terminate(stream.listener)

    # Installs signal handlers for handling SIGINT and SIGTERM
    # gracefully.
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)


def get_tweepy_auth(twitter_api_key,
                    twitter_api_secret,
                    twitter_access_token,
                    twitter_access_token_secret):
    """Make a tweepy auth object"""
    auth = tweepy.OAuthHandler(twitter_api_key, twitter_api_secret)
    auth.set_access_token(twitter_access_token, twitter_access_token_secret)
    return auth


def construct_listener(outfile=None):
    """Create the listener that prints tweets"""
    if outfile is not None:
        outfile = open(outfile, 'wb')

    return PrintingListener(out=outfile)

def should_continue():
    return True

def begin_stream_loop(stream, poll_interval):
    """Start and maintain the streaming connection..."""
    while should_continue():
        try:
            stream.start_polling(poll_interval)
        except Exception as e:
            # Infinite restart
            logger.error("Exception while polling. Restarting in 1 second.", exc_info=True)
            time.sleep(1)  # to avoid craziness


def start(track_file,
          twitter_api_key,
          twitter_api_secret,
          twitter_access_token,
          twitter_access_token_secret,
          poll_interval=15,
          unfiltered=False,
          languages=None,
          debug=False,
          outfile=None):
    """Start the stream."""
    listener = construct_listener(outfile)
    checker = BasicFileTermChecker(track_file, listener)

    auth = get_tweepy_auth(twitter_api_key,
                           twitter_api_secret,
                           twitter_access_token,
                           twitter_access_token_secret)

    stream = DynamicTwitterStream(auth, listener, checker, unfiltered=unfiltered, languages=languages)

    set_terminate_listeners(stream)
    if debug:
        set_debug_listener(stream)

    begin_stream_loop(stream, poll_interval)
