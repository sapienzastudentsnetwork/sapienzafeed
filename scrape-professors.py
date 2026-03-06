import requests
import json
import os

# URL of the original JSON
url = "https://raw.githubusercontent.com/sapienzastudentsnetwork/sapienzastudentsnetwork.github.io/refs/heads/main/data/teachers.json"

# Download the JSON
response = requests.get(url)
response.raise_for_status()
data = response.json()

# Build the new dictionary from the downloaded data
base_url = "https://corsidilaurea.uniroma1.it/it/lecturer/"
new_data = {uuid: {"name": info["name"].upper(), "url": f"{base_url}{uuid}"} for uuid, info in data.items()}

# Read existing professors.json if it exists
professors_file = "professors.json"
if os.path.exists(professors_file):
    with open(professors_file, "r", encoding="utf-8") as f:
        professors = json.load(f)
else:
    professors = {}

# Update or add professors from the new data
for uuid, info in new_data.items():
    professors[uuid] = info  # overwrite if already present, add if new

# Keep professors that were in professors.json but are no longer in the new data
# (no action needed, since we just overwrite/add without deleting)

# Save back to professors.json
with open(professors_file, "w", encoding="utf-8") as f:
    json.dump(professors, f, indent=2, ensure_ascii=False)
