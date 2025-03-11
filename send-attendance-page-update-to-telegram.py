import sys
import requests

# Get arguments from the command line
update_description = sys.argv[1]
file_url = sys.argv[2]
commit_url = sys.argv[3]
telegram_token = sys.argv[4]
chat_id = sys.argv[5]

# Format the message
update_description = update_description.replace("Update ", "<b>Content update</b> to ")

message = (
    f"📰 {update_description}\n\n"
    f"📄 View the <b>updated content</b>: {file_url}\n\n"
    f"🔍 View <b>changes</b>: {commit_url}"
)

# Send the message
url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
payload = {
    "chat_id": chat_id,
    "text": message,
    "parse_mode": "HTML"
}

response = requests.post(url, data=payload)

if response.status_code == 200:
    print("Message sent successfully!")
else:
    print(f"Failed to send message: {response.text}")
