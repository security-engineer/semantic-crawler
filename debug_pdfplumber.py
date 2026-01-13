
import io
import requests
import pdfplumber
from collections import Counter

# Target PDF: Interpretability in the Wild (IOI)
url = "https://arxiv.org/pdf/2211.00593.pdf"

def analyze_pdf(url):
    print(f"Downloading PDF from {url}...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
    except Exception as e:
        print(f"Error downloading: {e}")
        return

    print("Analyzing PDF with pdfplumber...")
    with pdfplumber.open(io.BytesIO(response.content)) as pdf:
        # 1. Analyze Font Sizes to find Body Text Size
        all_chars = []
        for page in pdf.pages[:3]: # Analyze first 3 pages
            all_chars.extend(page.chars)
        
        # Filter out spaces/empty
        sizes = [c['size'] for c in all_chars if c['text'].strip()]
        if not sizes:
            print("No text found.")
            return

        # Round sizes to 1 decimal place to handle slight variations
        sizes_rounded = [round(s, 1) for s in sizes]
        counter = Counter(sizes_rounded)
        
        print("\n--- Font Size Distribution (Top 10) ---")
        most_common_size, _ = counter.most_common(1)[0]
        for size, count in counter.most_common(10):
            print(f"Size {size}: {count} chars")
            
        print(f"\nEstimated Body Text Size: {most_common_size}")
        
        # 2. Print Lines with Font Info to visualize Headers
        print("\n--- Page Structure Analysis (First 2 Pages) ---")
        for i, page in enumerate(pdf.pages[:2]):
            print(f"\n=== Page {i+1} ===")
            # Extract words to easier grouping? Or just use extract_text with layout?
            # Let's inspect line-by-line using layout
            rows = page.extract_words(keep_blank_chars=True, use_text_flow=True, extra_attrs=['size', 'fontname'])
            
            # Group specific lines for readability in log
            # Simple grouping by top position
            current_top = -1
            line_buffer = []
            
            # Sort by top, then x0
            rows.sort(key=lambda x: (round(x['top']), x['x0']))
            
            lines = [] # Initialize lines list!
            
            for w in rows:
                if current_top == -1:
                    current_top = w['top']
                
                # New line detection (vertical dist)
                if abs(w['top'] - current_top) > 5:
                    if line_buffer:
                        lines.append(line_buffer)
                    line_buffer = []
                    current_top = w['top']
                
                # Horizontal Gap detection (split line into segments)
                elif line_buffer:
                    prev_w = line_buffer[-1]
                    gap = w['x0'] - prev_w['x1']
                    if gap > 15: # Threshold for column gap
                            lines.append(line_buffer)
                            line_buffer = []
                            current_top = w['top'] # Keep current_top for vertical alignment

                line_buffer.append(w)
            if line_buffer: lines.append(line_buffer)
            
            # Process lines (now segments)
            for line in lines:
                if not line: continue
                line_text = " ".join([w['text'] for w in line])
                
                    # Use Median size
                import statistics
                sizes_in_line = [w['size'] for w in line]
                avg_size = statistics.median(sizes_in_line)
                
                is_bold = "Bold" in line[0]['fontname'] or "CMBX" in line[0]['fontname']
                tag = "[HEADER CANDIDATE]" if avg_size >= most_common_size + 0.5 else "[Body]"  # Lowered threshold for debug
                
                if "Introduction" in line_text or "Executive Summary" in line_text or "Background" in line_text or "Model" in line_text:
                    tag = ">>> [POTENTIAL TARGET] <<< " + tag
                        
                print(f"{tag} Size:{avg_size:.1f} | {line_text[:80].encode('ascii', 'replace').decode('ascii')}...")

if __name__ == "__main__":
    analyze_pdf(url)
