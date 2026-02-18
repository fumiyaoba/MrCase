# import os
# from slack_sdk import WebClient
# from slack_sdk.errors import SlackApiError
# import env
# import get_time

# def get_channel_messages(): 
#     # # Initialize a Web API client
#     slack_token = env.SLACK_BOT_TOKEN
#     channel_id = env.SLACK_CHANNEL_ID

#     oldest = get_time.OLDEST

#     client = WebClient(token=slack_token)
#     print(type(client))
#     response = client.conversations_history(
#         channel = channel_id,
#         oldest = oldest
#         )

#     messages = response.get("messages", [])
#     return messages
#     for msg in messages:
#         text = msg.get("text", "")
#         if text.startswith("工数登録"):
#             print(text)
from slack_sdk import WebClient
import env
import get_time
from SlackMessage import SlackMessage

def get_channel_messages() -> list[SlackMessage]:
    client = WebClient(token=env.SLACK_BOT_TOKEN)

    response = client.conversations_history(
        channel=env.SLACK_CHANNEL_ID,
        oldest=get_time.OLDEST
    )

    messages = response.get("messages", [])

    return [
        SlackMessage(
            text=msg.get("text", ""),
            user=msg.get("user"),
            ts=msg["ts"],
            thread_ts=msg.get("thread_ts"),
            raw=msg
        )
        for msg in messages
    ]

messages = get_channel_messages()

filtered = [m for m in messages if m.text.startswith(env.ADD_MAN_HOUR)]
print(filtered)