# MRCASE/app/main.py
from MRCASE.app.slack_FileUpload import file_upload
from MRCASE.app.slack_ReadChannel import get_channel_messages
from MRCASE.app.filter import filter_by_first_line
from MRCASE.app.manhour_parser import parse_man_hour_message
from MRCASE import env
import MRCASE.app.excel_write as ex

def main():
    messages = get_channel_messages()

    filtered = filter_by_first_line(messages, env.ADD_MAN_HOUR)

    entries = []
    for msg in filtered:
        entries.extend(parse_man_hour_message(msg.text))
    ex.append_entries(entries, env.FILE, env.EXCEL_SHEET_RAW)
    file_upload(env.FILE)

if __name__ == "__main__":
    main()