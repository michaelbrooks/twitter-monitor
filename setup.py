from setuptools import setup

VERSION="0.3.0"

setup(
    name="twitter-monitor",
    packages=["twitter_monitor"],

    version=VERSION,
    download_url="https://github.com/michaelbrooks/twitter-monitor/archive/v%s.zip" % VERSION,
    url="https://github.com/michaelbrooks/twitter-monitor",

    author="Michael Brooks",
    author_email="mjbrooks@uw.edu",

    description=("A Twitter streaming library built on tweepy "
                 "that enables dynamic term tracking"),
    long_description=open("README.md").read(),
    license="MIT",
    keywords=["twitter", "streaming", "tweepy", "filter"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
    ],

    install_requires=[
        "tweepy >= 3.0"
    ],
    test_suite="tests",
    tests_require=["mock == 1.0.1"],
    scripts=["scripts/stream_tweets"],
)
