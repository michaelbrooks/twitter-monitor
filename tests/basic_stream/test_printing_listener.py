from unittest import TestCase
import logging
import mock
from twitter_monitor.basic_stream import PrintingListener

from StringIO import StringIO
import sys, os
import json
import time

logger = logging.getLogger("twitter_monitor")


class TestPrintingListener(TestCase):
    def setUp(self):
        logger.manager.disable = logging.CRITICAL
        self.out = StringIO()
        self.example_status = {"key": "value"}
        self.listener = PrintingListener(out=self.out)

    def test_defaults_to_stdout(self):
        listener = PrintingListener()
        self.assertEquals(listener.out, sys.stdout)

    def test_output_is_configurable(self):
        self.assertEquals(self.listener.out, self.out)

    def test_prints_on_status(self):
        """Tweet json should be printed"""

        self.listener.on_status(self.example_status)

        output = self.out.getvalue().strip()
        self.assertEquals(output, json.dumps(self.example_status))

    def test_prints_newlines_between_tweets(self):
        """There must be newlines between tweets"""

        num_tweets = 4
        tweet_json_text = json.dumps(self.example_status)
        expected_output = ""

        for i in range(num_tweets):
            self.listener.on_status(self.example_status)
            expected_output += tweet_json_text + os.linesep

        expected_output = expected_output.strip()
        output = self.out.getvalue().strip()
        self.assertEquals(output, expected_output)

    def test_counts_received_tweets(self):
        self.assertEquals(self.listener.received, 0)

        self.listener.on_status(self.example_status)
        self.assertEquals(self.listener.received, 1)

        self.listener.on_status(self.example_status)
        self.assertEquals(self.listener.received, 2)

    def test_allows_termination(self):
        # It should start out saying to continue
        go_on = self.listener.on_status(self.example_status)
        self.assertTrue(go_on)

        self.listener.set_terminate()

        # Now it should indicate to stop
        go_on = self.listener.on_status(self.example_status)
        self.assertFalse(go_on)

    @mock.patch('twitter_monitor.basic_stream.logger')
    def test_logs_statistics(self, logger):
        # Wait briefly post-creation
        time.sleep(0.1)

        self.listener.print_status()
        self.assertTrue(logger.info.called)

    def test_resets_received_after_stats(self):
        self.listener.received = 1
        self.listener.print_status()
        self.assertEquals(self.listener.received, 0)

