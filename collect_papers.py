
import json
import os
import re
import requests
import io
from semanticscholar import SemanticScholar
from pypdf import PdfReader

def sanitize_filename(filename):
    """
    Sanitize the filename to remove invalid characters.
    """
    return re.sub(r'[\\/*?:"<>|]', "", filename)

import datetime

def log(msg):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def extract_introduction(pdf_url, abstract_text=None):
    """
    Download PDF and extract the "Introduction" section.
    Returns the extracted text or None if failed.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        log(f"Attempting to download PDF from: {pdf_url}")
        
        try:
            response = requests.get(pdf_url, headers=headers, timeout=15, allow_redirects=True)
            
            if response.status_code == 403:
                log(f"Access Denied (403) for {pdf_url}. Likely anti-bot protection.")
                return None
            elif response.status_code != 200:
                log(f"Failed to download PDF. Status Code: {response.status_code}")
                return None
                
            log(f"Response received. Status: {response.status_code}")
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            log(f"Network request failed: {e}")
            return None
        
        content = response.content
        content_type = response.headers.get('Content-Type', '').lower()
        log(f"Content-Type: {content_type}, Content Length: {len(content)} bytes")

        # Handle HTML Landing Pages (finding hidden PDF link)
        if 'application/pdf' not in content_type and 'text/html' in content_type:
            log(f"Content-Type is '{content_type}'. Checking for direct PDF link in meta tags...")
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(content, 'html.parser')
                meta_pdf = soup.find('meta', attrs={'name': 'citation_pdf_url'})
                
                if meta_pdf and meta_pdf.get('content'):
                    real_pdf_url = meta_pdf['content']
                    log(f"Found real PDF URL in meta tag: {real_pdf_url}")
                    # Recursively call with the real PDF URL or just download
                    log(f"Downloading real PDF from: {real_pdf_url}")
                    response = requests.get(real_pdf_url, headers=headers, timeout=15)
                    log(f"Real PDF Response received. Status: {response.status_code}")
                    response.raise_for_status()
                    content = response.content
                    content_type = response.headers.get('Content-Type', '').lower()
                else:
                    log("No 'citation_pdf_url' meta tag found in HTML.")
                    return None
            except ImportError:
                log("BeautifulSoup not installed. Cannot parse HTML.")
                return None
            except Exception as e:
                log(f"Failed to parse HTML for PDF link: {e}")
                return None

        # Final check if we have a PDF
        if 'application/pdf' not in content_type:
            log(f"[WARNING] Final content-type is '{content_type}', not PDF. Skipping extraction.")
            return None

        with io.BytesIO(content) as f:
            reader = PdfReader(f)
            text = ""
            # Read first few pages (usually Introduction is in the first few pages)
            max_pages = min(len(reader.pages), 5)
            for i in range(max_pages):
                text += reader.pages[i].extract_text()
        
        # Define Stop Patterns for next sections
        # REFINED: Removed generic "2." to avoid matching list items (e.g. "2. Occurrences").
        # Now matches optional numbering (1., 2, I., II) followed by specific section titles.
        section_titles = [
            r'Literature Review',
            r'Related Work',
            r'Background',
            r'Preliminaries',
            r'Methodology',
            r'Method',
            r'The Proposed Method',
            r'System Model',
            r'Problem Formulation',
            r'Problem Statement',
            r'Significance of the study',
            r'Experimental Setup',
            r'Experiments',
            r'Results',
            r'Conclusion'
        ]
        titles_patt = "|".join(section_titles)
        # Pattern: \n \s* (?: (?: \d+\.? | [IVX]+\.? ) \s* )? (?: Title1 | ... ) \s* \n
        # Enforce that the title is the whole line (or ends the line) to avoid matching words in sentences.
        # Also add a generic stop for Roman Numerals (II. - X.) which are strong indicators of sections.
        
        specific_titles_patt = r'(?:(?:\d+\.?|[IVX]+\.?)\s*)?(?:' + titles_patt + r')\s*\n'
        roman_header_patt = r'(?:II|III|IV|V|VI|VII|VIII|IX|X)\.\s'
        
        stop_patterns = r'(?:' + specific_titles_patt + r'|' + roman_header_patt + r')'

        # Strategy 1: Standard Regex (Looking for "Introduction" header)
        # We changed stop_patterns to include the newline (in specific_titles_patt), so we adjust the lookahead key
        # REFINED: Added support for "I." (Roman numeral) prefix
        match = re.search(r'(?i)\n\s*(?:(?:1\.|I\.)\s*)?Introduction.*?\n(.*?)(?:\n\s*' + stop_patterns + r')', text, re.DOTALL)
        if match:
             return match.group(1).strip()

        # Strategy 2: Use Abstract to locate Introduction (Fallback)
        if abstract_text:
            log("Standard Regex failed. Attempting to use Abstract to locate Introduction...")
            # Normalize strings to improve matching (ignore whitespace differences)
            normalized_text = re.sub(r'\s+', ' ', text).lower()
            
            # Use the last 50 chars of the abstract to find its end position
            # This is more robust than matching the whole abstract
            abstract_chunk = abstract_text.strip()
            if len(abstract_chunk) > 50:
                abstract_chunk = abstract_chunk[-50:]
            normalized_chunk = re.sub(r'\s+', ' ', abstract_chunk).lower()
            
            idx = normalized_text.find(normalized_chunk)
            
            if idx == -1:
                 # Try even smaller chunk?
                 abstract_chunk = abstract_text.strip().split()[-5:] # Last 5 words
                 abstract_chunk = " ".join(abstract_chunk)
                 normalized_chunk = re.sub(r'\s+', ' ', abstract_chunk).lower()
                 idx = normalized_text.find(normalized_chunk)
                 if idx != -1:
                     log("Found Abstract end using last 5 words.")

            if idx != -1:
                # Approximate position in original text? 
                # Since we normalized, indices don't match. 
                # We need to find this chunk in the original text.
                # Construct a flexible regex from the chunk
                words = abstract_chunk.split()
                # Escape and allow whitespace between words
                pattern = r'\s*'.join([re.escape(w) for w in words])
                
                search_match = re.search(pattern, text, re.IGNORECASE)
                if search_match:
                    log("Found Abstract end in PDF.")
                    post_abstract_text = text[search_match.end():]
                    
                    # Define Stop Patterns again for this scope
                    section_titles = [
                        r'Literature Review',
                        r'Related Work',
                        r'Background',
                        r'Preliminaries',
                        r'Methodology',
                        r'Method',
                        r'The Proposed Method',
                        r'System Model',
                        r'Problem Formulation',
                        r'Problem Statement',
                        r'Significance of the study',
                        r'Experimental Setup',
                        r'Experiments',
                        r'Results',
                        r'Conclusion',
                        r'Model'
                    ]
                    titles_patt = "|".join(section_titles)
                    # Enforce end-of-line match
                    specific_titles_patt = r'(?:(?:\d+\.?|[IVX]+\.?)\s*)?(?:' + titles_patt + r')\s*\n'
                    roman_header_patt = r'(?:II|III|IV|V|VI|VII|VIII|IX|X)\.\s'
                    
                    stop_patterns = r'(?:' + specific_titles_patt + r'|' + roman_header_patt + r')'

                    # Search for standard OR spaced-out Introduction header
                    # "1. Introduction" or "1 I NTRODUCTION" or just "Introduction" or "I. Introduction"
                    # Flexible regex: I followed by space-opt N space-opt T...
                    intro_header_pattern = r'(?:(?:1\.|I\.)\s*)?(?:I\s*N\s*T\s*R\s*O\s*D\s*U\s*C\s*T\s*I\s*O\s*N|Introduction)'
                    
                    # Update regex to use new stop_patterns format
                    intro_match = re.search(r'(?i)\n\s*' + intro_header_pattern + r'.*?\n(.*?)(?:\n\s*' + stop_patterns + r')', post_abstract_text, re.DOTALL)
                    if intro_match:
                        return intro_match.group(1).strip()
                    
                    # Fallback: Just take everything up to the next section if header wasn't matched cleanly
                    # but we must be careful not to grab "Keywords" or metadata lines.
                    # Let's try to just find the START of the next section and take everything before it.
                    next_section_match = re.search(r'(?i)(\n\s*' + stop_patterns + r')', post_abstract_text, re.DOTALL)
                    if next_section_match:
                        # We have the end. Now where does it start? 
                        # Ideally after "Keywords" or just after the title/etc.
                        # Since we strictly started AFTER the abstract, the content is "between abstract and section 2".
                        # This INCLUDES the Introduction header line usually.
                        raw_content = post_abstract_text[:next_section_match.start()].strip()
                        
                        # Clean up "Keywords: ..." lines or similar junk at the start
                        # Also remove the "1. Introduction" line if it exists in the content
                        # Remove lines starting with "Keywords"
                        raw_content = re.sub(r'(?i)^keywords.*?\n', '', raw_content, flags=re.MULTILINE)
                        # Remove "1. Introduction" type headers if present at random places (unlikely if we missed it)
                        return raw_content.strip()

        # Fallback 3: Return text starting from "Introduction" (Truncation fallback)
        # Add support for Spaced Header here too
        match_start = re.search(r'(?i)\n\s*(?:1\.?)?\s*(?:I\s*N\s*T\s*R\s*O\s*D\s*U\s*C\s*T\s*I\s*O\s*N|Introduction).*?\n', text)
        if match_start:
            return text[match_start.end():].strip()
            
        return None

    except Exception as e:
        print(f"Failed to extract introduction from {pdf_url}: {e}")
        return None

def search_and_save(keyword, limit=5, output_dir='results'):
    """
    Search for papers by keyword and save them as JSON files.
    Only saves papers with open access PDFs.
    """
    sch = SemanticScholar(timeout=30)
    log(f"Searching for papers with keyword: '{keyword}'...")
    
    try:
        # We process indefinite results until we hit the user's limit of SAVED papers.
        # We set the API batch limit to 100 (max allowed) for efficiency.
        log(f"Querying Semantic Scholar API (fetching batches of 100)...")
        results = sch.search_paper(keyword, limit=100, fields=['title', 'abstract', 'url', 'openAccessPdf', 'externalIds'])
        log(f"API returned results object. Iterating...")
        
        if not results:
            log("No papers found.")
            return

        saved_count = 0
        
        # Ensure results directory exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Iterate through the paginated results
        for i, paper in enumerate(results):
            # Inform user if we are crossing a batch boundary (likely fetching next page)
            if i > 0 and i % 100 == 0:
                log(f"Processed {i} candidates. Fetching next batch if needed...")

            if saved_count >= limit:
                log(f"Reached limit of {limit} saved papers.")
                break

            pdf_url = None
            
            # log(f"Processing candidate {i+1}: {paper.title}") # Too verbose for large lists?
            
            # Priority 1: ArXiv
            if paper.externalIds and 'ArXiv' in paper.externalIds:
                arxiv_id = paper.externalIds['ArXiv']
                pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            
            # Priority 2: OpenAccessPDF
            elif paper.openAccessPdf and paper.openAccessPdf.get('url'):
                pdf_url = paper.openAccessPdf['url']
            
            if not pdf_url:
                # log(f"Skipping '{paper.title}': No PDF available.")
                continue

            log(f"Processing candidate {i+1} (Saved: {saved_count}): {paper.title}")
            log(f"PDF URL: {pdf_url}")

            abstract_text = paper.abstract
            # Extract Introduction
            log("Starting Introduction extraction...")
            introduction = extract_introduction(pdf_url, abstract_text)
            
            if not introduction:
                log(f"Skipping save: Introduction empty/failed for '{paper.title}'")
                continue # Skip saving if no introduction

            paper_data = {
                "title": paper.title,
                "keyword": keyword,
                "abstract": abstract_text,
                "pdf_link": pdf_url, 
                "introduction": introduction # REFACTOR: Renamed from 'introduce'
            }
            
            # Create a valid filename from the title
            filename = sanitize_filename(paper.title)
            # Truncate filename if too long
            if len(filename) > 100:
                filename = filename[:100]
                
            filepath = os.path.join(output_dir, f"{filename}.json")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(paper_data, f, ensure_ascii=False, indent=4)
            
            log(f"Saved: {filepath}")
            saved_count += 1
            
        log(f"Finished. Saved {saved_count} papers.")

    except Exception as e:
        log(f"An error occurred: {e}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Collect papers from Semantic Scholar.")
    parser.add_argument("keyword", type=str, nargs='?', help="Keyword to search for.")
    parser.add_argument("--limit", type=int, default=100, help="Number of papers to save (default: 10).")
    parser.add_argument("--output", type=str, default="gpt-2", help="Output directory for JSON files (default: 'results').")
    
    args = parser.parse_args()
    
    keyword = args.keyword
    if not keyword:
        keyword = input("Enter keyword to search: ")
    
    if keyword:
        search_and_save(keyword, limit=args.limit, output_dir=args.output)
    else:
        log("No keyword provided. Exiting.")
