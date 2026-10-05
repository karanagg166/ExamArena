#!/usr/bin/env python3
"""Optional manual smoke test script for Cohere answer key extraction.

Usage:
    export COHERE_API_KEY="your-api-key"
    python scripts/test_cohere_answer_key_extraction.py [path_to_sample_key.pdf]

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
from app.ai.extraction.answer_key import extract_answer_key_from_document
from app.ai.extraction.pdf import extract_pdf_document


SAMPLE_ANSWER_KEY_TEXT = """
Official Marking Scheme / Answer Key
Grade 10 Mathematics Midterm

Q1. (B) 4
Explanation: 2x + 6 = 14 => 2x = 8 => x = 4.

Q2. (C) 17
Explanation: 17 is a prime number divisible only by 1 and itself. 9 (3x3), 15 (3x5), and 21 (3x7) are composite.

Q3. y = 7
Marking Scheme / Rubric:
- Adding 5 to both sides to get 3y = 21: 2 Marks
- Dividing by 3 to get y = 7: 3 Marks
Total: 5 Marks
Explanation: 3y - 5 = 16 => 3y = 21 => y = 7.

Q4. (B) False
Explanation: All squares are rectangles, but not all rectangles are squares because a rectangle need not have all four sides equal.
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
        print(f"Reading provided answer key document: {pdf_path}")
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        doc = extract_pdf_document(pdf_bytes)
        print(f"Extracted {doc.page_count} pages, {len(doc.text)} characters.")
    else:
        print("Using synthetic sample answer key text...")
        page = PageContent(page_number=1, text=SAMPLE_ANSWER_KEY_TEXT, char_count=len(SAMPLE_ANSWER_KEY_TEXT))
        doc = ExtractedDocument(
            source_type=DocumentSourceType.PDF_TEXT,
            text=SAMPLE_ANSWER_KEY_TEXT,
            pages=[page],
            page_count=1,
        )

    print("Sending extraction request to Cohere with JSON Schema structured outputs...")
    answer_key, metrics = await extract_answer_key_from_document(doc, cohere_client=client)

    print("\n--- Answer Key Extraction Result ---")
    print(f"Exam Title Hint: {answer_key.exam_title or 'None'}")
    print(f"Total Answers Extracted: {len(answer_key.answers)}")
    print(f"Metrics: {metrics}")

    print("\n--- Extracted Answers ---")
    for ans in answer_key.answers:
        print(f"\nQ Ref: {ans.question_reference}")
        if ans.selected_option:
            print(f"  Selected Option: {ans.selected_option}")
        if ans.reference_answer:
            print(f"  Reference Answer: {ans.reference_answer}")
        if ans.rubric:
            print(f"  Rubric ({len(ans.rubric)} criteria):")
            for r in ans.rubric:
                print(f"    - {r.criterion}: {r.marks} marks")
        if ans.explanation:
            print(f"  Explanation: {ans.explanation}")
        if ans.confidence:
            print(f"  Confidence: {ans.confidence}")
        if ans.warnings:
            print(f"  Warnings: {ans.warnings}")

    print("\nCohere answer key extraction smoke test completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
