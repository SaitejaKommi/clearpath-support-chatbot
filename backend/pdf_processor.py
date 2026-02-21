#!/usr/bin/env python3
"""
PDF Processor - Extracts text from PDFs and creates intelligent chunks.
"""

import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any

try:
    import PyPDF2
except ImportError:
    print("Error: PyPDF2 not installed. Run: pip install PyPDF2")
    exit(1)


class PDFProcessor:
    """Processes PDF files and extracts text with intelligent chunking."""
    
    def __init__(self, pdf_dir: str = "./docs", output_dir: str = "./extracted_data", max_chunk_words: int = 400):
        """
        Initialize PDF processor.
        
        Args:
            pdf_dir: Directory containing PDF files
            output_dir: Directory to save extracted JSON files
            max_chunk_words: Maximum words per chunk
        """
        self.pdf_dir = Path(pdf_dir)
        self.output_dir = Path(output_dir)
        self.max_chunk_words = max_chunk_words
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"PDF Processor initialized")
        print(f"  Input:  {self.pdf_dir}")
        print(f"  Output: {self.output_dir}")
        print(f"  Max chunk size: {self.max_chunk_words} words")
    
    def extract_text_from_pdf(self, pdf_path: str) -> Dict[int, str]:
        """Extract text from PDF file, organized by page."""
        page_texts = {}
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages, start=1):
                    text = page.extract_text()
                    if text.strip():
                        page_texts[page_num] = text
            
            return page_texts
        
        except Exception as e:
            print(f"  ✗ Error extracting text: {e}")
            return {}
    
    def split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs based on double newlines."""
        # Split on double newlines
        paragraphs = re.split(r'\n\s*\n', text)
        
        cleaned = []
        for para in paragraphs:
            # Remove extra whitespace
            cleaned_para = ' '.join(para.split())
            if cleaned_para.strip():
                cleaned.append(cleaned_para)
        
        return cleaned
    
    def chunk_text(self, paragraphs: List[str]) -> List[str]:
        """Group paragraphs into chunks with maximum word count."""
        chunks = []
        current_chunk = []
        current_word_count = 0
        
        for paragraph in paragraphs:
            para_word_count = len(paragraph.split())
            
            # If adding this paragraph exceeds max, save current chunk
            if current_word_count + para_word_count > self.max_chunk_words and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [paragraph]
                current_word_count = para_word_count
            else:
                current_chunk.append(paragraph)
                current_word_count += para_word_count
        
        # Don't forget the last chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def process_pdf_file(self, pdf_path: str, filename: str) -> Dict[str, Any]:
        """Process a single PDF file."""
        print(f"\n  Processing: {filename}")
        
        # Extract text by page
        page_texts = self.extract_text_from_pdf(pdf_path)
        
        if not page_texts:
            print(f"    ✗ No text extracted")
            return None
        
        # Process all text together for chunking
        all_text = ' '.join(page_texts.values())
        paragraphs = self.split_into_paragraphs(all_text)
        chunks = self.chunk_text(paragraphs)
        
        # Create output structure
        output = {
            "file": filename,
            "total_pages": max(page_texts.keys()) if page_texts else 0,
            "chunks": []
        }
        
        # Add chunks with metadata
        for chunk_id, chunk_text in enumerate(chunks, start=1):
            page_num = self._estimate_page(chunk_text, page_texts)
            
            output["chunks"].append({
                "id": chunk_id,
                "text": chunk_text,
                "page": page_num,
                "word_count": len(chunk_text.split())
            })
        
        print(f"    ✓ Extracted {len(chunks)} chunks from {len(page_texts)} pages")
        return output
    
    def _estimate_page(self, chunk_text: str, page_texts: Dict[int, str]) -> int:
        """Estimate which page a chunk came from."""
        first_words = ' '.join(chunk_text.split()[:20])
        
        for page_num, page_text in page_texts.items():
            if first_words in page_text:
                return page_num
        
        return 1
    
    def process_all_pdfs(self) -> Dict[str, Any]:
        """Process all PDF files in the input directory."""
        if not self.pdf_dir.exists():
            print(f"\n✗ PDF directory not found: {self.pdf_dir}")
            return {}
        
        pdf_files = list(self.pdf_dir.glob("*.pdf"))
        
        if not pdf_files:
            print(f"\n✗ No PDF files found in {self.pdf_dir}")
            print(f"  Please add PDF files to: {self.pdf_dir}")
            return {}
        
        print(f"\n{'='*60}")
        print(f"Found {len(pdf_files)} PDF files to process")
        print(f"{'='*60}")
        
        all_documents = {}
        
        for pdf_path in sorted(pdf_files):
            result = self.process_pdf_file(str(pdf_path), pdf_path.name)
            if result:
                all_documents[pdf_path.name] = result
        
        return all_documents
    
    def save_to_json(self, data: Dict[str, Any], output_filename: str = "extracted_documents.json") -> str:
        """Save processed documents to JSON file."""
        output_path = self.output_dir / output_filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Combined data saved to: {output_path}")
        return str(output_path)
    
    def save_individual_files(self, documents: Dict[str, Any]) -> None:
        """Save each document as a separate JSON file."""
        for filename, doc_data in documents.items():
            output_filename = Path(filename).stem + "_extracted.json"
            output_path = self.output_dir / output_filename
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(doc_data, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Saved: {output_filename}")


def main():
    """Main execution function."""
    print("\n" + "="*60)
    print("PDF PROCESSOR - Extract & Chunk Documents")
    print("="*60)
    
    # Configuration
    PDF_DIRECTORY = "./docs"
    OUTPUT_DIRECTORY = "./extracted_data"
    MAX_CHUNK_WORDS = 400
    
    # Initialize processor
    processor = PDFProcessor(
        pdf_dir=PDF_DIRECTORY,
        output_dir=OUTPUT_DIRECTORY,
        max_chunk_words=MAX_CHUNK_WORDS
    )
    
    # Process all PDFs
    documents = processor.process_all_pdfs()
    
    if documents:
        # Save combined file
        processor.save_to_json(documents)
        
        # Save individual files
        print(f"\nSaving individual files:")
        processor.save_individual_files(documents)
        
        # Print summary
        print(f"\n" + "="*60)
        print("✓ PROCESSING COMPLETE")
        print("="*60)
        total_chunks = sum(len(doc.get("chunks", [])) for doc in documents.values())
        print(f"Total documents: {len(documents)}")
        print(f"Total chunks: {total_chunks}")
        print(f"\nSummary per document:")
        for filename, doc_data in documents.items():
            chunks = doc_data.get("chunks", [])
            if chunks:
                avg_words = sum(c.get("word_count", 0) for c in chunks) / len(chunks)
                print(f"  {filename}")
                print(f"    Chunks: {len(chunks)}, Avg words: {avg_words:.0f}")
        print("="*60 + "\n")
    else:
        print("\n✗ No documents were processed.")
        print("Please add PDF files to the ./docs directory and try again.")


if __name__ == "__main__":
    main()