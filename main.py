import sys
import argparse
import time
from pathlib import Path
from src.parser import RAGParser
from src.enricher import ContentEnricher
from src.utils import ensure_directory, extract_doi_metadata, save_text, save_json, save_yaml

def main():
    # 1. Argument Parsing
    parser = argparse.ArgumentParser(description="RAG-Refiner: PDF to Clean Markdown Pipeline")
    parser.add_argument("input_file", type=str, help="Path to the PDF file")
    args = parser.parse_args()

    input_path = Path(args.input_file).resolve()
    
    if not input_path.exists():
        print(f"Error: File {input_path} not found.")
        sys.exit(1)

    # 2. Setup Directories
    filename_no_ext = input_path.stem
    processed_dir = Path("data/processed") / filename_no_ext
    ensure_directory(processed_dir)

    print(f"--- Starting Processing for {input_path.name} ---")
    start_time = time.time()

    # 3. Parsing (Docling)
    rag_parser = RAGParser()
    try:
        markdown_content = rag_parser.process_pdf(input_path, processed_dir)
        save_text(markdown_content, processed_dir / "full_text.md")
        print("✅ Parsing & OCR complete. Markdown saved.")
    except Exception as e:
        print(f"❌ Parsing failed: {e}")
        sys.exit(1)

    # 4. DOI Extraction (pdf2doi)
    print("Extracting DOI metadata...")
    doi_data = extract_doi_metadata(input_path)
    
    # 5. Semantic Enrichment (Ollama)
    enricher = ContentEnricher(model="llama3.1")
    ai_metadata = enricher.enrich_content(markdown_content)

    # 6. Consolidate Metadata
    final_metadata = {
        "filename": input_path.name,
        "processed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "doi_info": doi_data,
        "ai_generated": ai_metadata
    }

    # Save Metadata in formats
    save_json(final_metadata, processed_dir / "metadata.json")
    save_yaml(final_metadata, processed_dir / "info.yaml")
    
    elapsed = time.time() - start_time
    print(f"✅ Processing complete in {elapsed:.2f}s")
    print(f"📂 Output location: {processed_dir}")

if __name__ == "__main__":
    main()