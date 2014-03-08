from setuptools import setup

setup(
    name="twitter-monitor",
    packages=['twitter_monitor'],

    version="0.1.1",
    download_url='https://github.com/michaelbrooks/twitter-monitor/archive/v0.1.1.zip',
    url="https://github.com/michaelbrooks/twitter-monitor",

    author="Michael Brooks",
    author_email="mjbrooks@uw.edu",

    description=("A Twitter streaming library built on tweepy "
                 "that enables dynamic term tracking"),
    long_description=open('README.md').read(),
    license="MIT",
    keywords=["twitter", "streaming", "tweepy", "filter"],
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