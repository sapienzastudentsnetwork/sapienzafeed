import sys
import requests

# Get arguments from the command line
professor_name = sys.argv[1]
file_url = sys.argv[2]
commit_url = sys.argv[3]
telegram_token = sys.argv[4]
chat_id = sys.argv[5]

# Format the message
message = (
    f"📰 <b>News update</b> for professor <b>{professor_name}</b> has been posted!\n\n"
    f"📄 View the <b>updated news</b>: {file_url}\n\n"
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
