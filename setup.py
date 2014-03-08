from setuptools import setup

setup(
    name="twitter-monitor",
    version="0.1.1",
    author="Michael Brooks",
    author_email="mjbrooks@uw.edu",
    description=("A Twitter streaming library built on tweepy "
                 "that enables dynamic term tracking"),
    license="MIT",
    keywords=["twitter", "streaming", "tweepy", "filter"],
    url="https://github.com/michaelbrooks/twitter-monitor",
    packages=['twitter_monitor'],
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