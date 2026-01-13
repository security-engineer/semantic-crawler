
import requests
from collect_papers import extract_introduction_font_aware, log

# Unleash GPT-2 Power for Event Detection
url = "https://aclanthology.org/2021.acl-long.490.pdf"

print(f"Downloading {url}...")
response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
content = response.content

print("Running Font-Aware Extraction...")
intro = extract_introduction_font_aware(content)

if intro:
    print("\n--- EXTRACTED INTRODUCTION ---")
    print(intro[-1000:].encode('cp949', errors='ignore').decode('cp949')) # LAST 1000 chars to check ending
    print("...")
else:
    print("Extraction Failed!")
