# RAG-Refiner 📝

A "Human-in-the-loop" pipeline to convert raw PDFs into high-quality, metadata-enriched Markdown for RAG (Retrieval Augmented Generation) systems.

## Features
* **Parsing:** Uses `docling` for OCR and table extraction.
* **Enrichment:** Uses local `Ollama` (Llama 3.1) to generate keywords, summaries, and citations.
* **GUI:** Streamlit interface to review text, check images, and edit metadata before saving.
* **Output:** Clean Markdown with YAML Frontmatter + Extracted Images.

## Installation

1.  **Prerequisites:** Ubuntu (WSL2), Python 3.10+, Ollama.
2.  **Setup:**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/RAG-Refiner.git](https://github.com/YOUR_USERNAME/RAG-Refiner.git)
    cd RAG-Refiner
    chmod +x setup.sh
    ./setup.sh
    ```

## Usage

1.  Activate environment: `source venv/bin/activate`
2.  Run the App:
    ```bash
    streamlit run app.py
    ```
3.  Open browser to `http://localhost:8501`.
4.  Drag & Drop a PDF -> Review -> Save.