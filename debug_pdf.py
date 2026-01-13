import urllib.request
from pypdf import PdfReader
import io
import re
from bs4 import BeautifulSoup

# Target PDF URL (HTML page)
url = "https://www.mdpi.com/2306-5354/11/6/521"

# Headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Referer': 'https://www.google.com/'
}

if __name__ == "__main__":
    print(f"Accessing URL: {url}")
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            print(f"Status Code: {response.getcode()}")
            content_type = response.info().get_content_type()
            print(f"Content-Type: {content_type}")

            content = response.read()
            soup = BeautifulSoup(content, 'html.parser')
            
            # MDPI usually puts sections in <section> or <div> with classes
            # Look for Introduction header
            print("\n--- Searching HTML for Introduction ---")
            
            # Common patterns for MDPI or general HTML
            # Check for header tags
            headers = soup.find_all(['h1', 'h2', 'span'], string=re.compile(r'Introduction', re.IGNORECASE))
            for h in headers:
                print(f"Found header: <{h.name}> {h.get_text().strip()}")
                # Try to get content after
                # This depends heavily on structure.
                # MDPI often uses <section class="html-section">
                parent_section = h.find_parent('section')
                if parent_section:
                    print("Found parent section!")
                    text = parent_section.get_text()
                    print(f"Section text start: {text[:200]}")
                    break
                else:
                    # Maybe it's a flat structure?
                    print("No parent section found. Checking siblings...")
            
            print("\n--- Extracting Text from Body ---")
            # Fallback: Just dump text and check
            text = soup.get_text()
            idx = text.lower().find("introduction")
            if idx != -1:
                print(f"Introduction word found at {idx}")
                print(text[idx:idx+500])
            else:
                print("Introduction word NOT found in text.")

    except Exception as e:
        print(f"Error: {e}")

    except Exception as e:
        print(f"Error: {e}")
