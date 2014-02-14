
class TermChecker(object):
    """
    Responsible for managing the current set of tracked terms
    and checking for updates.

    This is intended to be extended.
    """

    def __init__(self):
        self._tracking_terms_set = set()


    def update_tracking_terms(self):
        """
        Retrieve the current set of tracked terms from wherever it is stored.
        Subclasses may check in files, databases, etc...

        Should return a set of strings.
        """
        return set(['#afakehashtag'])

    def reset(self):
        """
        Clear the list of tracked terms.
        """
        self._tracking_terms_set = set()

    def check(self):
        """
        Checks if the list of tracked terms has changed.
        Returns True if changed, otherwise False.
        """

        new_tracking_terms = self.update_tracking_terms()

        terms_changed = False

        # any deleted terms?
        if self._tracking_terms_set > new_tracking_terms:
            terms_changed = True

        # any added terms?
        elif self._tracking_terms_set < new_tracking_terms:
            terms_changed = True

        # Go ahead and store for later
        self._tracking_terms_set = new_tracking_terms

        # If the terms changed, we need to restart the stream
        return terms_changed

    def tracking_terms(self):
        """
        Get the current list of tracked terms.
        """
        return list(self._tracking_terms_set)


class FileTermChecker(TermChecker):
    """
    Checks for tracked terms in a file.
    """

    def __init__(self, filename):
        super(FileTermChecker, self).__init__()
        self.filename = filename

    def update_tracking_terms(self):
        with open(self.filename) as input:
            # read all the lines
            lines = input.readlines()

            # build a set of terms
            new_terms = {line.strip() for line in lines}

            return new_terms
