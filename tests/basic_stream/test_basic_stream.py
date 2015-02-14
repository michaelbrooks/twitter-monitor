from unittest import TestCase
import logging
import mock
from twitter_monitor import basic_stream
import tweepy

logger = logging.getLogger("twitter_monitor")

# A mock of the signal module without SIGUSR
class FakeSignal(object):
    signal = mock.Mock()


class TestBasicStreamSignals(TestCase):
    def setUp(self):
        logger.manager.disable = logging.CRITICAL

    @mock.patch('twitter_monitor.basic_stream.signal')
    def test_set_debug_listener(self, signal):
        """Should set a signal for SIGUSR1 when SIGUSR1 is available"""
        stream = mock.Mock()

        signal.SIGUSR1 = 254323

        self.assertFalse(signal.signal.called)

        basic_stream.set_debug_listener(stream)

        self.assertEquals(signal.signal.call_count, 1)

        args, kwargs = signal.signal.call_args
        self.assertEquals(len(args), 2)
        self.assertEquals(args[0], signal.SIGUSR1)
        self.assertTrue(hasattr(args[1], '__call__'))  # 2nd arg should be a callback

    @mock.patch('twitter_monitor.basic_stream.signal', new_callable=FakeSignal)
    @mock.patch('twitter_monitor.basic_stream.logger')
    def test_set_debug_listener(self, loggerMock, signal):
        """Should NOT set a signal for SIGUSR1 when not available"""
        stream = mock.Mock()

        self.assertFalse(signal.signal.called)
        self.assertFalse(loggerMock.warn.called)

        basic_stream.set_debug_listener(stream)

        self.assertFalse(signal.signal.called)
        self.assertTrue(loggerMock.warn.called)

    @mock.patch('traceback.format_stack')
    @mock.patch('code.InteractiveConsole')
    def test_launch_debugger(self, InteractiveConsole, format_stack):
        """Should break into an interactive debugger."""

        interactive_obj = mock.Mock()
        formatted_stack = ['1', '2', '3']

        InteractiveConsole.return_value = interactive_obj
        format_stack.return_value = formatted_stack

        frame = mock.Mock()
        frame.f_globals = {}
        frame.f_locals = {}

        stream = mock.Mock()

        basic_stream.launch_debugger(frame, stream=stream)

        self.assertEquals(InteractiveConsole.call_count, 1)
        format_stack.assert_called_once_with(frame)
        self.assertEquals(interactive_obj.interact.call_count, 1)

    @mock.patch('twitter_monitor.basic_stream.signal')
    def test_set_terminate_listeners(self, signal):
        """Should set SIGTERM and SIGINT listeners"""

        signal.SIGTERM = 235
        signal.SIGINT = 468

        stream = mock.Mock()
        basic_stream.set_terminate_listeners(stream)

        self.assertEquals(signal.signal.call_count, 2)

        signals = [args[0] for args, kwargs in signal.signal.call_args_list]

        self.assertSetEqual(set(signals), set([signal.SIGTERM, signal.SIGINT]))

    def test_terminate(self):
        """Should stop the listener and raise a SystemExit"""

        listener = mock.Mock()
        with self.assertRaises(SystemExit):
            basic_stream.terminate(listener)
        self.assertTrue(listener.set_terminate.called)


class TestBasicStream(TestCase):
    def setUp(self):
        logger.manager.disable = logging.CRITICAL

    @mock.patch('twitter_monitor.basic_stream.PrintingListener')
    def test_construct_listener_with_file(self, PrintingListener):
        PrintingListener.return_value = 53234

        outfile = "some_file.txt"

        mock_open = mock.mock_open()
        mock_open.return_value = 348374387
        with mock.patch('twitter_monitor.basic_stream.open', mock_open, create=True):
            result = basic_stream.construct_listener(outfile)

        mock_open.assert_called_once_with(outfile, 'wb')

        PrintingListener.assert_called_once_with(out=mock_open.return_value)
        self.assertEquals(result, PrintingListener.return_value)

    def test_get_tweepy_auth(self):
        twitter_api_key = 'ak'
        twitter_api_secret = 'as'
        twitter_access_token = 'at'
        twitter_access_token_secret = 'ats'
        result = basic_stream.get_tweepy_auth(twitter_api_key,
                                              twitter_api_secret,
                                              twitter_access_token,
                                              twitter_access_token_secret)
        self.assertIsInstance(result, tweepy.OAuthHandler)

        self.assertEquals(result.consumer_key, twitter_api_key)
        self.assertEquals(result.consumer_secret, twitter_api_secret)
        self.assertEquals(result.access_token, twitter_access_token)
        self.assertEquals(result.access_token_secret, twitter_access_token_secret)


    @mock.patch('twitter_monitor.basic_stream.should_continue')
    @mock.patch('twitter_monitor.basic_stream.logger')
    @mock.patch('twitter_monitor.basic_stream.time')
    def test_begin_stream_loop(self, time, loggerMock, should_continue):
        """It catches exceptions."""

        # Stop looping after 3 times
        desired_loop_count = 3

        def check():
            print "Loop # %d" % should_continue.call_count
            if should_continue.call_count >= desired_loop_count:
                return False

            return True

        should_continue.side_effect = check

        poll_interval = 0.1
        stream = mock.Mock()

        def polling_fn(pi):
            self.assertEquals(pi, poll_interval)
            if should_continue.call_count == 2:
                raise Exception("Testing!")

        stream.start_polling.side_effect = polling_fn

        basic_stream.begin_stream_loop(stream, poll_interval)

        self.assertEquals(should_continue.call_count, desired_loop_count)
        self.assertEquals(stream.start_polling.call_count, desired_loop_count - 1)
        self.assertEquals(loggerMock.error.call_count, 1)
        time.sleep.assert_called_once_with(1)
