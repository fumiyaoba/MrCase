# MRCASE/app/main.py

from MRCASE.app.slack_ReadChannel import get_channel_messages
from MRCASE.app.filter import filter_by_first_line
from MRCASE.app.manhour_parser import parse_man_hour_message
from MRCASE import env
from MRCASE.app.excel_write import append_entries_to_excel   

def main():
    messages = get_channel_messages()

    filtered = filter_by_first_line(messages, env.ADD_MAN_HOUR)

    entries = []
    for msg in filtered:
        entries.extend(parse_man_hour_message(msg.text))
    
    append_entries_to_excel(entries, env.FILE)
    print(f"saved to excel: {env.FILE}")

if __name__ == "__main__":
    main()
