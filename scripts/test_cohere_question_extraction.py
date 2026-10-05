#!/usr/bin/env python3
"""Optional manual smoke test script for Cohere question paper extraction.

Usage:
    export COHERE_API_KEY="your-api-key"
    python scripts/test_cohere_question_extraction.py [path_to_sample.pdf]

DO NOT run during automated CI or pytest.
Never commit API keys into source control.
"""

import asyncio
import os
import sys

# Ensure backend is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.ai.clients.cohere_client import CohereClient
from app.ai.extraction.document import ExtractedDocument, PageContent, DocumentSourceType
from app.ai.extraction.question_paper import extract_questions_from_document
from app.ai.extraction.pdf import extract_pdf_document


SAMPLE_PAPER_TEXT = """
Mathematics Midterm Examination - Grade 10
Duration: 60 Minutes | Total Marks: 50
Instructions: Answer all questions. Each question indicates its marks.

Section A: Multiple Choice Questions (2 Marks each)

1. What is the value of x if 2x + 6 = 14?
A. 2
B. 4
C. 6
D. 8

2. Which of the following is a prime number?
A. 9
B. 15
C. 17
D. 21

Section B: Short Answer Questions (5 Marks each)

3. Solve for y: 3y - 5 = 16. Show all intermediate calculation steps. [5 Marks]

4. Is the statement 'Every rectangle is a square' True or False?
A. True
B. False
"""


async def main():
    api_key = os.getenv("COHERE_API_KEY")
    if not api_key:
        print("ERROR: COHERE_API_KEY environment variable is not set.")
        print("Please set COHERE_API_KEY before running this manual smoke test.")
        sys.exit(1)

    print(f"Initializing CohereClient with model={os.getenv('COHERE_MODEL', 'command-r-plus')}...")
    client = CohereClient(api_key=api_key)

    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        pdf_path = sys.argv[1]
        print(f"Reading provided PDF: {pdf_path}")
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        doc = extract_pdf_document(pdf_bytes)
        print(f"Extracted {doc.page_count} pages, {len(doc.text)} characters.")
    else:
        print("Using synthetic sample examination text...")
        page = PageContent(page_number=1, text=SAMPLE_PAPER_TEXT, char_count=len(SAMPLE_PAPER_TEXT))
        doc = ExtractedDocument(
            source_type=DocumentSourceType.PDF_TEXT,
            text=SAMPLE_PAPER_TEXT,
            pages=[page],
            page_count=1,
        )

    print("Sending extraction request to Cohere with JSON Schema structured outputs...")
    paper, metrics = await extract_questions_from_document(doc, cohere_client=client)

    print("\nExtraction Success!")
    print(f"Title: {paper.title}")
    print(f"Subject: {paper.subject}")
    print(f"Total Marks: {paper.total_marks}")
    print(f"Duration: {paper.duration_minutes} minutes")
    print(f"Extracted Questions Count: {len(paper.questions)}")
    print(f"Metrics: {metrics}")

    print("\n--- Extracted Questions ---")
    for q in paper.questions:
        print(f"\n[{q.question_type}] Q{q.question_number}: {q.text} ({q.marks} Marks) [Confidence: {q.confidence}]")
        if q.section:
            print(f"  Section: {q.section}")
        for opt in q.options:
            print(f"    {opt.label or '-'}: {opt.text} (is_correct={opt.is_correct})")
        if q.warnings:
            print(f"  Warnings: {q.warnings}")


if __name__ == "__main__":
    asyncio.run(main())
