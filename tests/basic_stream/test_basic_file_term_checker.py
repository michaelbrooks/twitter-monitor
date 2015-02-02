from unittest import TestCase
import logging
import mock
from twitter_monitor.basic_stream import BasicFileTermChecker

logger = logging.getLogger("twitter_monitor")

class TestBasicFileTermChecker(TestCase):

    def setUp(self):
        logger.manager.disable = logging.CRITICAL        
        self.listener = mock.Mock()
        self.checker = BasicFileTermChecker(filename="testfile", listener=self.listener)

    @mock.patch("twitter_monitor.checker.FileTermChecker.update_tracking_terms")
    def test_prints_status(self, super_update_tracking_terms):
        self.assertFalse(self.listener.print_status.called)

        self.checker.update_tracking_terms()

        self.assertTrue(self.listener.print_status.called)
        self.assertTrue(super_update_tracking_terms.called)
