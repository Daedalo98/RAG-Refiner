import os
import json
import yaml
import pdf2doi
from pathlib import Path
from typing import Dict, Any, List

def ensure_directory(path: Path) -> None:
    """Creates directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)

def extract_doi_metadata(pdf_path: Path) -> Dict[str, Any]:
    """Uses pdf2doi to extract identifier info."""
    try:
        result = pdf2doi.pdf2doi(str(pdf_path))
        return {
            "doi": result.get('identifier'),
            "validation_info": result.get('validation_info')
        }
    except Exception as e:
        return {"error": str(e), "doi": None}

def save_markdown_with_frontmatter(
    path: Path, 
    content: str, 
    metadata: Dict[str, Any]
) -> None:
    """
    Saves content to a file with YAML frontmatter.
    Structure:
    ---
    key: value
    ---
    
    # Document Content
    """
    # Clean up metadata for YAML dumping
    # Ensure keywords are a list, not a string
    if isinstance(metadata.get('keywords'), str):
        metadata['keywords'] = [k.strip() for k in metadata['keywords'].split(',') if k.strip()]

    # Dump metadata to YAML string
    yaml_header = yaml.dump(metadata, sort_keys=False, allow_unicode=True).strip()
    
    final_file_content = f"---\n{yaml_header}\n---\n\n{content}"
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(final_file_content)