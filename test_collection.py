
import os
import shutil
import glob
import json
from collect_papers import search_and_save

def test_search_and_save():
    # Setup: Clear results directory
    if os.path.exists('results'):
        shutil.rmtree('results')
    os.makedirs('results')

    keyword = "Deep Learning" # Using a broad keyword to ensure we find papers with PDFs
    limit = 2
    
    print(f"Running test with keyword: '{keyword}' and limit: {limit}")
    search_and_save(keyword, limit=limit)
    
    # Verification
    json_files = glob.glob(os.path.join('results', '*.json'))
    print(f"Found {len(json_files)} JSON files in results directory.")
    
    if len(json_files) > 0:
        print("Test PASSED: Files created.")
        for f in json_files:
            print(f"- {f}")
            with open(f, 'r', encoding='utf-8') as json_file:
                data = json.load(json_file)
                if not data.get('pdf_link'):
                    print("  [ERROR] 'pdf_link' is empty!")
                else:
                    print(f"  [OK] 'pdf_link': {data['pdf_link']}")
                
                if not data.get('introduce'):
                    print("  [ERROR] 'introduce' is empty!")
                else:
                    intro_sample = data['introduce'][:50].replace('\n', ' ')
                    print(f"  [OK] 'introduce' start: {intro_sample}...")

    else:
        print("Test FAILED: No files created.")

if __name__ == "__main__":
    test_search_and_save()
