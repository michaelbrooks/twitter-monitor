from unittest import TestCase
import threading
import time
import mock

from twitter_monitor import DynamicTwitterStream


class TestDynamicTwitterStream(TestCase):
    def setUp(self):

        # Mock tweepy.Stream
        self.stream_patcher = mock.patch('tweepy.Stream')
        self.MockTweepyStream = self.stream_patcher.start()
        self.tweepy_stream_instance = mock.Mock()
        self.MockTweepyStream.return_value = self.tweepy_stream_instance

        # Mock the supporting objects
        self.auth = mock.Mock()
        self.listener = mock.Mock()
        self.checker = mock.Mock()

        # For controlling the tracking terms
        self.term_list = []
        self.checker.tracking_terms.return_value = self.term_list

        self.stop_timeout = DynamicTwitterStream.STOP_TIMEOUT
        DynamicTwitterStream.STOP_TIMEOUT = 0
        self.retry_count = 7

        # Create a dynamic twitter stream
        self.stream = DynamicTwitterStream(auth=self.auth,
                                           listener=self.listener,
                                           term_checker=self.checker,
                                           retry_count=self.retry_count)

    def tearDown(self):
        self.stream_patcher.stop()

        # Restore the normal stop timeout
        DynamicTwitterStream.STOP_TIMEOUT = self.stop_timeout

    def test_start_stream_no_terms(self):

        # Start the stream without a term
        self.stream.start_stream()

        # Should check the list of terms
        self.checker.tracking_terms.assert_called_once_with()

        # A stream should NOT have been created, because no terms yet
        self.MockTweepyStream.assert_has_calls([])

    def test_start_stream_with_terms(self):

        # Start the stream with a term
        self.term_list.append("hello")
        self.stream.start_stream()

        # Should check the list of terms
        self.checker.tracking_terms.assert_called_once_with()

        # Should create a Stream instance
        self.MockTweepyStream.assert_called_once_with(self.auth, self.listener,
                                                      stall_warnings=True,
                                                      timeout=90,
                                                      retry_count=self.retry_count)
        # Should start the filter with the terms
        self.tweepy_stream_instance.filter.assert_called_once_with(track=self.term_list, async=True)


    def test_stop_stream_not_started(self):

        self.stream.stop_stream()

        # No attempt to disconnect stream that isn't started
        self.tweepy_stream_instance.disconnect.assert_has_calls([])


    def test_stop_stream_started(self):

        # Start the stream with a term
        self.term_list.append("hello")
        self.stream.start_stream()

        self.stream.stop_stream()

        # Should try to disconnect tweepy stream
        self.tweepy_stream_instance.disconnect.assert_called_once_with()

    def test_update_stream_terms_unchanged(self):

        self.checker.check.return_value = False

        self.stream.start_stream = mock.Mock()
        self.stream.stop_stream = mock.Mock()

        self.stream.update_stream()

        # Should have checked if terms changed
        self.checker.check.assert_called_once_with()

        # Should NOT have stopped the old stream
        self.assertEqual(self.stream.stop_stream.call_count, 0)

        # Should NOT have started a new stream
        self.assertEqual(self.stream.start_stream.call_count, 0)

    def test_update_stream_terms_changed(self):

        self.checker.check.return_value = True

        self.stream.start_stream = mock.Mock()
        self.stream.stop_stream = mock.Mock()

        self.stream.update_stream()

        # Should have checked if terms changed
        self.checker.check.assert_called_once_with()

        # Should NOT have stopped the old stream
        self.stream.stop_stream.assert_called_once_with()

        # Should NOT have started a new stream
        self.stream.start_stream.assert_called_once_with()

    def test_handle_exceptions(self):

        self.listener.streaming_exception = None

        try:
            self.stream.handle_exceptions()
        except Exception:
            self.fail("Raised exception when no streaming exception set")

        self.listener.streaming_exception = Exception("testing")
        self.assertRaises(Exception, self.stream.handle_exceptions)

    def test_stop_polling(self):

        # Mock some supporting methods we test separately
        self.stream.update_stream = mock.Mock()
        self.stream.handle_exceptions = mock.Mock()

        # This should poll every 1 second
        thread = threading.Thread(target=self.stream.start_polling, args=[1])
        thread.start()

        waits = 0
        # Wait for a maximum of 3 seconds (ish), or until the loop has run at least once
        while self.stream.update_stream.call_count < 2 and waits < 12:
            print "Waiting..."
            time.sleep(0.25)
            waits += 1

        self.assertTrue(self.stream.polling)

        # Try to stop the thread
        self.stream.stop_polling()

        self.assertFalse(self.stream.polling)

        # Wait for a maximimum of 2 seconds
        thread.join(timeout=2)

        self.assertGreaterEqual(self.stream.update_stream.call_count, 1, "Checked for stream/term updates")
        self.assertGreaterEqual(self.stream.handle_exceptions.call_count, 1, "Checked for stream exceptions")



