import threading
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
    STOP_TIMEOUT = 60

    def __init__(self, auth, listener, term_checker):
        self.auth = auth
        self.listener = listener
        self.term_checker = term_checker
        self.tracking_terms = []

        self.polling = False
        self.stream = None
        self.streaming_thread = None
        self.stream_exception = None
        self.polling_interrupt = threading.Event()

    # Called by the outer term polling thread
    def start(self, interval):
        self.polling = True
        self.stream_exception = None

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
            if self.stream_exception is not None:
                # propagate outward
                raise self.stream_exception

            # wait for the interval unless interrupted
            try:
                self.polling_interrupt.wait(interval)
            except KeyboardInterrupt:
                tlog("Polling canceled by user")
                return

        tlog("Term poll ceased!")

    # Called by the outer term polling thread
    def update_stream(self):
        """
        Restarts the stream with the current list of tracking terms.
        """

        # Stop any old stream
        self.stop_stream()

        if len(self.tracking_terms) > 0:
            # we have terms to track, so build a new stream

            self.stream = tweepy.Stream(self.auth, self.listener, stall_warnings=True, timeout=90)

            # Launch it in a new thread
            self.streaming_thread = threading.Thread(target=self._launch_stream)
            self.streaming_thread.start()

    # Called by the outer term polling thread
    def stop_stream(self):
        """
        Stops the current stream. Blocks until this is done.
        """

        if self.stream is not None:
            # There is a streaming thread

            tlog("Stopping twitter stream...")
            self.stream.disconnect()
            self.stream = None

            # wait a few seconds to allow the streaming to actually stop
            try:
                # But up to 60 seconds
                self.polling_interrupt.wait(self.STOP_TIMEOUT)

            except KeyboardInterrupt:
                tlog("Polling cancelled by user.")

    # Meant to be run in the streaming thread
    def _launch_stream(self):

        # Reset the stream exception tracker
        self.stream_exception = None

        # Get updated terms
        tlog("Starting new twitter stream with %s terms" % (len(self.tracking_terms)))
        tlog(self.tracking_terms)

        # Run the stream
        try:
            self.stream.filter(track=self.tracking_terms, async=False)
            raise Exception("Twitter stream filter returned")
        except Exception, exception:
            tlog("Forwarding exception from streaming thread.")
            self.stream_exception = exception

        finally:

            # Interrupt the main polling thread so it can decide what to do
            if self.polling_interrupt is not None:
                self.polling_interrupt.set()
                self.polling_interrupt.clear()

            tlog("Twitter stream stopped.")