from slack_sdk import WebClient
from MRCASE import env
from MRCASE.app import get_time
from MRCASE.models.slack_message import SlackMessage

def get_channel_messages() -> list[SlackMessage]:
    client = WebClient(token=env.SLACK_BOT_TOKEN)

    response = client.conversations_history(
        channel=env.SLACK_CHANNEL_ID,
        oldest=get_time.OLDEST
    )

    messages = response.get("messages", [])

    return [
        SlackMessage(
            text=msg.get(env.KEY_TEXT, env.VALUE_EMPTY),
            user=msg.get(env.KEY_USER),
            ts=msg[env.KEY_TS],
            thread_ts=msg.get(env.KEY_THREAD_TS),
            raw=msg
        )
        for msg in messages
    ]
