# MRCASE/app/main.py

from MRCASE.app.slack_ReadChannel import get_channel_messages
from MRCASE.app.filter import filter_by_first_line
from MRCASE.app.manhour_parser import parse_man_hour_message
from MRCASE import env
from MRCASE.app.excel_write import pick_message_with_text       

def main():
    messages = get_channel_messages()
    print(f"all messages count: {len(messages)}")

    filtered = filter_by_first_line(messages, env.ADD_MAN_HOUR)
    print(f"filtered messages count: {len(filtered)}")

    print("----- filtered messages -----")
    for msg in filtered:
        print(msg.text)
        print("----------------------------")

    # ★ ここから parser の確認
    entries = []
    for msg in filtered:
        entries.extend(parse_man_hour_message(msg.text))

    print(f"entries count: {len(entries)}")
    print("----- parsed entries -----")
    for e in entries:
        print(e)
    print("--------------------------")

if __name__ == "__main__":
    main()
