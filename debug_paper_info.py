
from semanticscholar import SemanticScholar
import json

sch = SemanticScholar()
title = "ET-BERT: A Contextualized Datagram Representation with Pre-training Transformers for Encrypted Traffic Classification"

print(f"Searching for: {title}")
results = sch.search_paper(title, limit=1, fields=['title', 'url', 'openAccessPdf', 'externalIds'])

if results:
    paper = results[0]
    print(f"Title: {paper.title}")
    print(f"OpenAccessPDF: {paper.openAccessPdf}")
    print(f"External IDs: {paper.externalIds}")
    
    # Check if there are other URLs
    # Semantic scholar library objects might have more fields if we ask
else:
    print("Paper not found.")
