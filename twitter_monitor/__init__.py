import threading

def tlog(msg):
    """A logging mechanism that adds the current thread to the output"""
    print "%s (t %s)" %(msg, thread_id())

def thread_id():
    """Returns the current thread id."""
    return threading.current_thread().ident

from checker import TermChecker
from stream import DynamicTwitterStream
from listener import JsonStreamListener