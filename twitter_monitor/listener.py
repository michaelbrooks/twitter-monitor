import json
import logging

from tweepy.streaming import StreamListener


logger = logging.getLogger(__name__)


class JsonStreamListener(StreamListener):
    """
    This extends the Tweepy StreamListener to avoid
    closing the streaming connection when certain bad events occur.

    Also skips construction of Tweepy's "Status" object since you might
     use your own class anyway. Just leaves it a parsed JSON object.

    Extending this would allow more conscientious handling of rate
     limit messages or other errors, for example.
    """

    def __init__(self, api=None):
        super(JsonStreamListener, self).__init__(api)
        self.streaming_exception = None

    def on_data(self, data):
        try:
            entity = json.loads(data)
            if not isinstance(entity, dict):
                logger.error("Non-object received: %s", data, exc_info=True)

                return True
        except ValueError:
            logger.error("Invalid data received: %s", data, exc_info=True)
            return True

        if 'delete' in entity:
            status = entity['delete']['status']
            return self.on_delete(status['id'], status['user_id'])

        elif 'scrub_geo' in entity:
            scrub_geo = entity['scrub_geo']
            return self.on_scrub_geo(scrub_geo['user_id'], scrub_geo['up_to_status_id'])

        elif 'limit' in entity:
            limit = entity['limit']
            return self.on_limit(limit['track'])

        elif 'status_withheld' in entity:
            status = entity['status_withheld']
            return self.on_status_withheld(status['id'], status['user_id'], status['withheld_in_countries'])

        elif 'user_withheld' in entity:
            user = entity['user_withheld']
            return self.on_user_withheld(user['id'], user['withheld_in_countries'])

        elif 'disconnect' in entity:
            disconnect = entity['disconnect']
            return self.on_disconnect(disconnect['code'], disconnect['stream_name'], disconnect['reason'])

        elif 'warning' in entity:
            warning = entity['warning']
            return self.on_stall_warning(warning['code'], warning['message'], warning['percent_full'])

        elif 'in_reply_to_status_id' in entity:
            return self.on_status(entity)
        else:
            return self.on_unknown(entity)

    def on_status(self, status):
        """Called when a new status arrives"""
        logger.info("Status %s received", status['id'])
        return True

    def on_delete(self, status_id, user_id):
        """Called when a delete notice arrives for a status"""
        logger.info("Delete %s received", status_id)
        return True

    def on_scrub_geo(self, user_id, up_to_status_id):
        """Called when geolocated data must be stripped for user_id for statuses before up_to_status_id"""
        logger.info("Scrub_geo received for user %s", user_id)
        return True

    def on_limit(self, track):
        """Called when a limitation notice arrvies"""
        logger.warn('Limit received for %s', track)
        return True

    def on_status_withheld(self, status_id, user_id, countries):
        """Called when a status is withheld"""
        logger.warn('Status %s withheld for user %s', status_id, user_id)
        return True

    def on_user_withheld(self, user_id, countries):
        """Called when a user is withheld"""
        logger.warn('User %s withheld', user_id)
        return True

    def on_disconnect(self, code, stream_name, reason):
        """Called when a disconnect is received"""
        logger.error('Disconnect message: %s %s %s', code, stream_name, reason)
        return True

    def on_stall_warning(self, code, message, percent_full):
        logger.warn("Stall warning (%s): %s (%s%% full)", code, message, percent_full)
        return True

    def on_error(self, status_code):
        """Called when a non-200 status code is returned"""
        logger.error('Twitter returned error code %s', status_code)
        return False

    def on_unknown(self, entity):
        """Called when an unrecognized object arrives"""
        logger.error('Unknown object received: %s', repr(entity))
        return True

    def on_exception(self, exception):
        """An exception occurred in the streaming thread"""
        logger.error('Exception from stream!', exc_info=True)
        self.streaming_exception = exception