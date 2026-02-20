from pathlib import Path
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import MRCASE.env as env

# Initialize a Web API client
slack_token = env.SLACK_BOT_TOKEN
channel_id = env.SLACK_CHANNEL_ID

def file_upload(excel_filepath: str | Path):
    client = WebClient(token=slack_token)

    # Call the chat.postMessage method
    try:
        response = client.files_upload_v2(
            channel = channel_id,
            file = excel_filepath
        )
        print("OK: uploaded")
    except SlackApiError as e:
        print("NG:", e.response["error"])
        assert e.response["error"]