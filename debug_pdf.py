import urllib.request
from pypdf import PdfReader
import io
import re
from bs4 import BeautifulSoup

# Target PDF URL (Radicalization Risks of GPT-3)
url = "https://arxiv.org/pdf/2009.06807.pdf"

# Headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

if __name__ == "__main__":
    print(f"Downloading PDF from: {url}")
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            print(f"Status Code: {response.getcode()}")
            content_type = response.info().get_content_type()
            print(f"Content-Type: {content_type}")

            if content_type == 'application/pdf':
                content = response.read()
                with io.BytesIO(content) as f:
                    reader = PdfReader(f)
                    text = ""
                    for page in reader.pages[:5]:
                        text += page.extract_text()
                    
                    print("\n--- Extracted Text (First 3000 chars) ---")
                    print(text[:3000].encode('ascii', errors='replace').decode('ascii'))
                    
                     # Define abstract_text locally
                    abstract_text = "In this paper, we expand on our previous research of the potential for abuse of generative language models by assessing GPT-3. Experimenting with prompts representative of different types of extremist narrative, structures of social interaction, and radical ideologies, we find that GPT-3 demonstrates significant improvement over its predecessor, GPT-2, in generating extremist texts. We also show GPT-3's strength in generating text that accurately emulates interactive, informational, and influential content that could be utilized for radicalizing individuals into violent far-right extremist ideologies and behaviors. While OpenAI's preventative measures are strong, the possibility of unregulated copycat technology represents significant risk for large-scale online radicalization and recruitment; thus, in the absence of safeguards, successful and efficient weaponization that requires little experimentation is likely. AI stakeholders, the policymaking community, and governments should begin investing as soon as possible in building social norms, public policy, and educational initiatives to preempt an influx of machine-generated disinformation and propaganda. Mitigation will require effective policy and partnerships across industry, government, and civil society."

    except Exception as e:
        print(f"Error: {e}")

    except Exception as e:
        print(f"Error: {e}")
