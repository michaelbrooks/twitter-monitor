import unittest
import tempfile
import os
import logging

from twitter_monitor.checker import TermChecker, FileTermChecker


logger = logging.getLogger("twitter_monitor")


class ListChecker(TermChecker):
    """
    Basic term checker that checks a list of terms.
    Add/remove terms to this list externally.
    """

    def __init__(self, list):
        super(ListChecker, self).__init__()
        self._list = list

    def update_tracking_terms(self):
        return set(self._list)


class TestDefaultTermChecker(unittest.TestCase):
    """This mostly just exists to get 100% test coverage..."""

    def test_default_implementation(self):
        checker = TermChecker()
        self.assertTrue(checker.check())


class TestTermChecker(unittest.TestCase):
    def setUp(self):
        logger.manager.disable = logging.CRITICAL

        self.term_list = []
        self.checker = ListChecker(self.term_list)

    def test_tracking_terms_start(self):
        self.assertEqual(self.checker.tracking_terms(), list(), "Checker starts with no terms")
    
    def test_tracking_terms_add(self):
        # Put a term in the list
        self.term_list.append("my term")
        terms = self.checker.tracking_terms()
        self.assertEqual(terms, [], "No terms returned before check called")

        # Check and discover the new term
        self.checker.check()
        terms = self.checker.tracking_terms()
        self.assertEqual(terms, ["my term"], "After check, term registered")

    def test_tracking_terms_remove(self):
        # Put a term in the checker
        self.term_list.append("my term")
        self.checker.check()

        # Remove the term
        self.term_list.remove("my term")
        terms = self.checker.tracking_terms()
        self.assertEqual(terms, ["my term"], "Before check, no change in terms returned")

        # Now check and discover the removal
        self.checker.check()
        terms = self.checker.tracking_terms()
        self.assertEqual(terms, [], "After check, term removed")

    def test_check(self):
        self.assertFalse(self.checker.check(), "check returns False before term added")
        self.term_list.append("my term")
        self.assertTrue(self.checker.check(), "check returns True after term added")
        self.assertFalse(self.checker.check(), "check returns False again")

        self.term_list.remove("my term")
        self.assertTrue(self.checker.check(), "check returns True after term removed")
        self.assertFalse(self.checker.check(), "check returns False again")

    def test_reset(self):
        # Add a term and check
        self.term_list.append("my term")
        self.checker.check()

        # Now reset the checker
        self.checker.reset()
        terms = self.checker.tracking_terms()
        self.assertEqual(terms, [], "Reset empties the checker")


class TestFileTermChecker(unittest.TestCase):
    def setUp(self):
        self.file = tempfile.NamedTemporaryFile(delete=False)
        self.file.close()

        self.checker = FileTermChecker(self.file.name)

    def test_update_tracked_terms(self):
        terms = self.checker.update_tracking_terms()
        self.assertEqual(terms, set(), "Returns empty set if file is empty")

        with open(self.file.name, mode='w+b') as tfile:
            tfile.write("one\n")
            tfile.write("two three\n")
            tfile.write("two three\n")
            tfile.write("  four  \n")
            tfile.write("\n")
            tfile.write("\tfive; six\'\t\n")

        terms = self.checker.update_tracking_terms()
        self.assertEqual(terms,
                         set(["one", "two three", "four", "five; six'"]),
                         "Read terms from the file: %s" % repr(terms))

    def tearDown(self):
        self.file.close()
        os.unlink(self.file.name)
