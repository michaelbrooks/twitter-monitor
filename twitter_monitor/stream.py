import threading
from time import sleep, time
import logging

import tweepy

logger = logging.getLogger(__name__)


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

        self.polling = False
        self.stream = None

        self.polling_interrupt = threading.Event()

        self.retry_count = options.get("retry_count", 5)


    def start_polling(self, interval):
        """
        Start polling for term updates and streaming.
        """

        self.polling = True

        # clear the stored list of terms - we aren't tracking any
        self.term_checker.reset()

        logger.info("Starting polling for changes to the track list")
        while self.polling:

            loop_start = time()

            self.update_stream()
            self.handle_exceptions()

            # wait for the interval unless interrupted, compensating for time elapsed in the loop
            elapsed = time() - loop_start
            self.polling_interrupt.wait(max(0.1, interval - elapsed))

        logger.warn("Term poll ceased!")

    def stop_polling(self):
        """Halts the polling loop and streaming"""
        logger.info("Stopping polling loop")

        self.polling = False
        self.polling_interrupt.set()
        self.polling_interrupt.clear()

        self.stop_stream()

    def update_stream(self):
        """
        Restarts the stream with the current list of tracking terms.
        """

        # Check if the tracking list has changed
        if not self.term_checker.check():
            return

        # Stop any old stream
        self.stop_stream()

        # Start a new stream
        self.start_stream()

    def start_stream(self):
        """Starts a stream with teh current tracking terms"""

        tracking_terms = self.term_checker.tracking_terms()

        if len(tracking_terms) > 0:
            # we have terms to track, so build a new stream
            self.stream = tweepy.Stream(self.auth, self.listener,
                                        stall_warnings=True,
                                        timeout=90,
                                        retry_count=self.retry_count)

            logger.info("Starting new twitter stream with %s terms:", (len(tracking_terms)))
            logger.info("  %s", repr(tracking_terms))

            # Launch it in a new thread
            self.stream.filter(track=tracking_terms, async=True)

    def stop_stream(self):
        """
        Stops the current stream. Blocks until this is done.
        """

        if self.stream is not None:
            # There is a streaming thread

            logger.warn("Stopping twitter stream...")
            self.stream.disconnect()

            self.stream = None

            # wait a few seconds to allow the streaming to actually stop
            sleep(self.STOP_TIMEOUT)

    def handle_exceptions(self):
        # check to see if an exception was raised in the streaming thread
        if self.listener.streaming_exception is not None:
            logger.warn("Streaming exception: %s", self.listener.streaming_exception)
            # propagate outward
            raise self.listener.streaming_exception
