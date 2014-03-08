from unittest import TestCase
import logging
import mock
from twitter_monitor import JsonStreamListener

logger = logging.getLogger("twitter_monitor")


class TestJsonStreamListener(TestCase):
    def setUp(self):
        logger.manager.disable = logging.CRITICAL

        self.listener = JsonStreamListener()

    def test_on_exception(self):
        self.assertTrue(self.listener.streaming_exception is None)

        try:
            raise Exception("testing")
        except Exception, exception:
            self.listener.on_exception(exception)

        self.assertEquals(self.listener.streaming_exception, exception, "Saves exception")

    def test_on_error(self):
        self.assertFalse(self.listener.on_error(404))

    def test_on_status(self):
        fake_status = dict(id=12345652)
        self.assertTrue(self.listener.on_status(fake_status))


class TestStreamListenerHandling(TestCase):
    def setUp(self):
        logger.manager.disable = logging.CRITICAL

        self.listener = JsonStreamListener()

        # Patch a bunch of methods on the listener so we can check
        # the handling of different message types
        self.patched_methods = ['on_status', 'on_delete', 'on_scrub_geo',
                                'on_limit', 'on_status_withheld', 'on_user_withheld',
                                'on_disconnect', 'on_stall_warning',
                                'on_error', 'on_unknown', 'on_exception']

        for patch in self.patched_methods:
            replacement = mock.Mock(wraps=getattr(self.listener, patch))
            mock.patch.object(self.listener, patch, replacement).start()


    def test_on_data_bad_json(self):
        """Nothing gets called when bad data is provided."""

        bad_json = "{asdfn35w3 asdkjnfw aksjnlka;;asd;f;a3lkjn"
        self.assertTrue(self.listener.on_data(bad_json), "Continues despite bad json")

        # Should have called NONE of the patched handler methods
        for patch in self.patched_methods:
            self.assertEquals(getattr(self.listener, patch).call_count, 0, "Does not call %s" % patch)

    def test_on_data_list_json(self):
        """Nothing gets called when the data represents a list."""

        list_json = '["foo", "bar"]'
        self.assertTrue(self.listener.on_data(list_json), "Continues despite list-like json")

        # Should have called NONE of the patched handler methods
        for patch in self.patched_methods:
            self.assertEquals(getattr(self.listener, patch).call_count, 0, "Does not call %s" % patch)

    def test_on_data_string_json(self):
        """Nothing gets called when the data represents a string."""

        string_json = '"foo"'
        self.assertTrue(self.listener.on_data(string_json), "Continues despite string-like json")

        # Should have called NONE of the patched handler methods
        for patch in self.patched_methods:
            self.assertEquals(getattr(self.listener, patch).call_count, 0, "Does not call %s" % patch)

    def test_on_data_delete(self):
        """Delete message"""
        delete_json = """{
          "delete":{
            "status":{
              "id":1234,
              "id_str":"1234",
              "user_id":3,
              "user_id_str":"3"
            }
          }
        }"""
        self.assertTrue(self.listener.on_data(delete_json))
        self.listener.on_delete.assert_called_once_with(1234, 3)

    def test_on_data_scrub_geo(self):
        """scrub_geo message"""
        scrub_geo = """{
          "scrub_geo":{
            "user_id":14090452,
            "user_id_str":"14090452",
            "up_to_status_id":23260136625,
            "up_to_status_id_str":"23260136625"
          }
        }"""
        self.assertTrue(self.listener.on_data(scrub_geo))
        self.listener.on_scrub_geo.assert_called_once_with(14090452, 23260136625)

    def test_on_data_limit(self):
        """limit message"""
        limit = """{
          "limit":{
            "track":1234
          }
        }"""

        self.assertTrue(self.listener.on_data(limit))
        self.listener.on_limit.assert_called_once_with(1234)

    def test_on_data_status_withheld(self):
        """status_withheld message"""
        status_withheld = """{
          "status_withheld":{
            "id":1234567890,
            "user_id":123456,
            "withheld_in_countries":["DE", "AR"]
          }
        }"""

        self.assertTrue(self.listener.on_data(status_withheld))
        self.listener.on_status_withheld.assert_called_once_with(1234567890, 123456, ["DE", "AR"])

    def test_on_data_user_withheld(self):
        """user_withheld message"""
        user_withheld = """{
          "user_withheld":{
            "id":123456,
            "withheld_in_countries":["DE","AR"]
          }
        }"""

        self.assertTrue(self.listener.on_data(user_withheld))
        self.listener.on_user_withheld.assert_called_once_with(123456, ["DE", "AR"])

    def test_on_data_disconnect(self):
        """disconnect message"""
        disconnect = """{
          "disconnect":{
            "code": 4,
            "stream_name":"test_stream",
            "reason":"Some reason"
          }
        }"""

        self.assertTrue(self.listener.on_data(disconnect))
        self.listener.on_disconnect.assert_called_once_with(4, "test_stream", "Some reason")

    def test_on_data_stall_warning(self):
        """stall_warning message"""
        stall_warning = """{
          "warning":{
            "code":"FALLING_BEHIND",
            "message":"Your connection is falling behind.",
            "percent_full": 60
          }
        }"""

        self.assertTrue(self.listener.on_data(stall_warning))
        self.listener.on_stall_warning.assert_called_once_with("FALLING_BEHIND",
                                                               "Your connection is falling behind.", 60)

    def test_on_data_status(self):
        """status message"""
        status = r"""{
          "coordinates": null,
          "created_at": "Sat Sep 10 22:23:38 +0000 2011",
          "truncated": false,
          "favorited": false,
          "id_str": "112652479837110273",
          "entities": {
            "urls": [
              {
                "expanded_url": "http://instagr.am/p/MuW67/",
                "url": "http://t.co/6J2EgYM",
                "indices": [
                  67,
                  86
                ],
                "display_url": "instagr.am/p/MuW67/"
              }
            ],
            "hashtags": [
              {
                "text": "tcdisrupt",
                "indices": [
                  32,
                  42
                ]
              }
            ],
            "user_mentions": [
              {
                "name": "Twitter",
                "id_str": "783214",
                "id": 783214,
                "indices": [
                  0,
                  8
                ],
                "screen_name": "twitter"
              },
              {
                "name": "Picture.ly",
                "id_str": "334715534",
                "id": 334715534,
                "indices": [
                  15,
                  28
                ],
                "screen_name": "SeePicturely"
              },
              {
                "name": "Bosco So",
                "id_str": "14792670",
                "id": 14792670,
                "indices": [
                  46,
                  58
                ],
                "screen_name": "boscomonkey"
              },
              {
                "name": "Taylor Singletary",
                "id_str": "819797",
                "id": 819797,
                "indices": [
                  59,
                  66
                ],
                "screen_name": "episod"
              }
            ]
          },
          "in_reply_to_user_id_str": "783214",
          "text": "@twitter meets @seepicturely at #tcdisrupt cc.@boscomonkey @episod http://t.co/6J2EgYM",
          "contributors": null,
          "id": 112652479837110273,
          "retweet_count": 0,
          "in_reply_to_status_id_str": null,
          "geo": null,
          "retweeted": false,
          "possibly_sensitive": false,
          "in_reply_to_user_id": 783214,
          "place": null,
          "source": "<a href=\"http://instagr.am\" rel=\"nofollow\">Instagram</a>",
          "user": {
            "profile_sidebar_border_color": "eeeeee",
            "profile_background_tile": true,
            "profile_sidebar_fill_color": "efefef",
            "name": "Eoin McMillan ",
            "profile_image_url": "http://a1.twimg.com/profile_images/1380912173/Screen_shot_2011-06-03_at_7.35.36_PM_normal.png",
            "created_at": "Mon May 16 20:07:59 +0000 2011",
            "location": "Twitter",
            "profile_link_color": "009999",
            "follow_request_sent": null,
            "is_translator": false,
            "id_str": "299862462",
            "favourites_count": 0,
            "default_profile": false,
            "url": "http://www.eoin.me",
            "contributors_enabled": false,
            "id": 299862462,
            "utc_offset": null,
            "profile_image_url_https": "https://si0.twimg.com/profile_images/1380912173/Screen_shot_2011-06-03_at_7.35.36_PM_normal.png",
            "profile_use_background_image": true,
            "listed_count": 0,
            "followers_count": 9,
            "lang": "en",
            "profile_text_color": "333333",
            "protected": false,
            "profile_background_image_url_https": "https://si0.twimg.com/images/themes/theme14/bg.gif",
            "description": "Eoin's photography account. See @mceoin for tweets.",
            "geo_enabled": false,
            "verified": false,
            "profile_background_color": "131516",
            "time_zone": null,
            "notifications": null,
            "statuses_count": 255,
            "friends_count": 0,
            "default_profile_image": false,
            "profile_background_image_url": "http://a1.twimg.com/images/themes/theme14/bg.gif",
            "screen_name": "imeoin",
            "following": null,
            "show_all_inline_media": false
          },
          "in_reply_to_screen_name": "twitter",
          "in_reply_to_status_id": null
        }"""

        import json

        status_obj = json.loads(status)

        self.assertTrue(self.listener.on_data(status))
        self.listener.on_status.assert_called_once_with(status_obj)

    def test_on_data_unknown(self):
        """Unknown message"""
        unknown = """{
          "something":{
            "that":"i",
            "made":"up"
          }
        }"""

        import json

        unknown_obj = json.loads(unknown)

        self.assertTrue(self.listener.on_data(unknown))
        self.listener.on_unknown.assert_called_once_with(unknown_obj)
