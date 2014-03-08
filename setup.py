import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="twitter-monitor",
    version="0.1.1",
    author="Michael Brooks",
    author_email="mjbrooks@uw.edu",
    description=("A Twitter streaming library built on tweepy "
                 "that enables dynamic term tracking"),
    license="MIT",
    keywords="Twitter streaming",
    url="https://github.com/michaelbrooks/twitter-monitor",
    packages=['twitter_monitor'],
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
    ],
    install_requires=[
        "tweepy >= 2.2"
    ],
    test_suite="tests",
    tests_require=["mock == 1.0.1"]
)