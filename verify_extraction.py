
import requests
from collect_papers import extract_introduction_font_aware, log

url = "https://arxiv.org/pdf/2009.06807.pdf"

print(f"Downloading {url}...")
response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
content = response.content

print("Running Font-Aware Extraction...")
intro = extract_introduction_font_aware(content)

if intro:
    print("\n--- EXTRACTED INTRODUCTION ---")
    print(intro[:1000].encode('cp949', errors='ignore').decode('cp949')) # First 1000 chars
    print("...")
else:
    print("Extraction Failed!")
