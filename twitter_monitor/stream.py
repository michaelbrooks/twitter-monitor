import threading
from time import sleep
import tweepy
from . import tlog


class DynamicTwitterStream(object):
    """
    A wrapper around Tweepy's Stream class that causes
    streaming to be executed in a secondary thread.

    Meanwhile the primary thread sleeps for an interval between checking for
    term list updates.
    """

    # Number of seconds to wait for the stream to stop
    STOP_TIMEOUT = 1

    def __init__(self, auth, listener, term_checker, **options):
        self.auth = auth
        self.listener = listener
        self.term_checker = term_checker

        self.tracking_terms = []
        self.polling = False
        self.stream = None

        self.polling_interrupt = threading.Event()

        self.retry_count = options.get("retry_count", 5)


    def start(self, interval):
        """
        Start polling for term updates and streaming.
        """

        self.polling = True

        # clear the stored list of terms - we aren't tracking any
        self.term_checker.reset()

        # there is no Stream object running yet
        self.stream = None

        tlog("Starting polling for changes to the track list")
        while self.polling:

            # Check if the tracking list has changed
            if self.term_checker.check():
                # There were changes to the term list -- restart the stream
                self.tracking_terms = self.term_checker.tracking_terms()
                self.update_stream()

            # check to see if an exception was raised in the streaming thread
            if self.listener.stream_exception is not None:
                # propagate outward
                raise self.listener.stream_exception

            # wait for the interval unless interrupted
            try:
                self.polling_interrupt.wait(interval)
            except KeyboardInterrupt:
                tlog("Polling canceled by user")
                return

        tlog("Term poll ceased!")

    def update_stream(self):
        """
        Restarts the stream with the current list of tracking terms.
        """

        # Stop any old stream
        self.stop_stream()

        if len(self.tracking_terms) > 0:
            # we have terms to track, so build a new stream

            self.stream = tweepy.Stream(self.auth, self.listener,
                                        stall_warnings=True,
                                        timeout=90,
                                        retry_count=self.retry_count)

            tlog("Starting new twitter stream with %s terms" % (len(self.tracking_terms)))
            tlog(self.tracking_terms)

            # Launch it in a new thread
            self.stream.filter(track=self.tracking_terms, async=True)

    def stop_stream(self):
        """
        Stops the current stream. Blocks until this is done.
        """

        if self.stream is not None:
            # There is a streaming thread

            tlog("Stopping twitter stream...")
            self.stream.disconnect()

            # wait a few seconds to allow the streaming to actually stop
            sleep(self.STOP_TIMEOUT)
