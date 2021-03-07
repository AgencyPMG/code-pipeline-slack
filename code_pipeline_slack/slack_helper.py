from slack_sdk import WebClient
from datetime import datetime
from datetime import timedelta

import os
import json
import logging

logger = logging.getLogger()

LOGLEVEL = os.environ.get("LOGLEVEL", "WARNING").upper()
logging.basicConfig(level=LOGLEVEL)


class SlackHelper:

    CHANNEL_CACHE = {}
    MESSAGE_CACHE = {}

    def __init__(self, token, channel_name, channel_type, bot_name, bot_icon):
        self.client = WebClient(token=token)
        self.channel_name = channel_name
        self.channel_type = channel_type
        self.bot_name = bot_name
        self.bot_icon = bot_icon

    def find_channel(self, name):
        if name in SlackHelper.CHANNEL_CACHE:
            return SlackHelper.CHANNEL_CACHE[name]

        r = self.client.conversations_list(exclude_archived=1, types=self.channel_type)

        if "error" in r:
            logger.error(
                "error getting channel with name '" + name + "': {}".format(r["error"])
            )
        else:
            for ch in r["channels"]:
                if ch["name"] == name:
                    SlackHelper.CHANNEL_CACHE[name] = (ch["id"], ch["is_private"])
                    return SlackHelper.CHANNEL_CACHE[name]

        return None, None

    def find_my_messages(self, ch_name, user_name=None):
        ch_id, is_private = self.find_channel(ch_name)

        if user_name is None:
            user_name = self.bot_name

        if not ch_id:
            logger.error("error getting channel")
            return

        print("Channel id = ", ch_id)

        history = self.client.conversations_history(
            channel=ch_id, oldest=(datetime.now() - timedelta(hours=2)).timestamp()
        )

        if "error" in history:
            logger.error(
                "error fetching history for channel {}: {}".format(
                    ch_id, history["error"]
                )
            )
        else:
            for m in history["messages"]:
                if m.get("username") == user_name:
                    logger.debug("Found message: ", m)
                    yield m

    def find_message_for_build(self, execution_id):
        cached = SlackHelper.MESSAGE_CACHE.get(execution_id)

        if cached:
            return cached

        for m in self.find_my_messages(self.channel_name):
            for att in self.message_attachments(m):
                if att.get("footer") == execution_id:
                    SlackHelper.MESSAGE_CACHE[execution_id] = m
                    return m

        return None

    def message_attachments(self, message):
        return message.get("attachments", [])

    def message_fields(self, message):
        for att in self.message_attachments(message):
            for f in att["fields"]:
                yield f

    def post_build_message(self, message, message_id, execution_id):
        import pdb; pdb.set_trace()

        ch_id, is_private = self.find_channel(self.channel_name)
        logger.debug("Channel id = ", ch_id)

        # update existing message
        if message_id:
            logger.debug("Updating existing message")

            r = self.update_message(ch_id, message_id, message)
            logger.debug(json.dumps(r, indent=2))

            if r["ok"]:
                r["message"]["ts"] = r["ts"]
                SlackHelper.MESSAGE_CACHE[execution_id] = r[
                    "message"
                ]

            return r

        logger.debug("New message")
        r = self.send_message(ch_id, message)

        return r

    def send_message(self, ch, attachments):
        r = self.client.chat_postMessage(
            channel=ch,
            icon_emoji=self.bot_icon,
            username=self.bot_name,
            attachments=attachments,
        )

        return r

    def update_message(self, ch, ts, attachments):
        r = self.client.chat_update(
            channel=ch,
            ts=ts,
            icon_emoji=self.bot_icon,
            username=self.bot_name,
            attachments=attachments,
        )

        return r
