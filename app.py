import streamlit as st
import ollama
import shutil
import tempfile
import time
from pathlib import Path
from streamlit_pdf_viewer import pdf_viewer

# Import backend logic
from src.parser import RAGParser
from src.enricher import ContentEnricher
from src.utils import extract_doi_metadata, save_markdown_with_frontmatter, ensure_directory

st.set_page_config(page_title="RAG-Refiner", page_icon="📝", layout="wide")

# --- Helper Functions ---
def get_ollama_models():
    """Fetches available local models."""
    try:
        models_info = ollama.list()
        if hasattr(models_info, 'models'):
            raw_models = models_info.models
        elif isinstance(models_info, dict) and 'models' in models_info:
            raw_models = models_info['models']
        else:
            return ["llama3.1"]

        model_names = []
        for m in raw_models:
            if hasattr(m, 'model'):
                model_names.append(m.model)
            elif hasattr(m, 'name'):
                model_names.append(m.name)
            elif isinstance(m, dict):
                model_names.append(m.get('model', m.get('name')))
        return [m for m in model_names if m]
    except Exception:
        return ["llama3.1"]

def reset_session():
    st.session_state.processed_data = None
    st.session_state.temp_pdf_path = None
    # Ensure this key exists to avoid errors on first load
    if "editor_markdown" in st.session_state:
        del st.session_state.editor_markdown

# --- Main App ---
def main():
    if "processed_data" not in st.session_state:
        reset_session()
    if "temp_dir" not in st.session_state:
        st.session_state.temp_dir = tempfile.mkdtemp()

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        available_models = get_ollama_models()
        selected_model = st.selectbox("Ollama Model", options=available_models, index=0 if available_models else None)
        if st.button("Reset / New File"):
            reset_session()
            st.rerun()

    st.title("📝 RAG-Refiner: Edit & Preview")

    # --- UPLOAD VIEW ---
    if not st.session_state.processed_data:
        uploaded_file = st.file_uploader("Drag and drop a PDF", type=["pdf"])
        
        if uploaded_file and st.button("🚀 Process Document"):
            with st.spinner("Parsing PDF and Generating Metadata..."):
                try:
                    # 1. Save to Temp
                    temp_path = Path(st.session_state.temp_dir)
                    input_pdf_path = temp_path / uploaded_file.name
                    with open(input_pdf_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    # 2. Parse (Docling)
                    parser = RAGParser()
                    markdown_text = parser.process_pdf(input_pdf_path, temp_path)

                    # 3. Enrich (Ollama)
                    enricher = ContentEnricher(model=selected_model)
                    ai_metadata = enricher.enrich_content(markdown_text)

                    # 4. DOI
                    doi_data = extract_doi_metadata(input_pdf_path)

                    # 5. Save to State
                    st.session_state.temp_pdf_path = str(input_pdf_path)
                    st.session_state.processed_data = {
                        "filename": uploaded_file.name,
                        "stem": Path(uploaded_file.name).stem,
                        "markdown": markdown_text,
                        "ai_metadata": ai_metadata,
                        "doi_data": doi_data,
                        "temp_path": str(temp_path)
                    }
                    # Initialize the editor state
                    st.session_state.editor_markdown = markdown_text
                    st.rerun()

                except Exception as e:
                    st.error(f"Processing failed: {e}")

    # --- REVIEW VIEW (Split Screen) ---
    else:
        col_pdf, col_work = st.columns([1, 1])
        data = st.session_state.processed_data

        # === LEFT PANEL: PDF ===
        with col_pdf:
            st.info(f"📄 Source: {data['filename']}")
            if st.session_state.temp_pdf_path:
                pdf_viewer(st.session_state.temp_pdf_path, height=900)

        # === RIGHT PANEL: Workspace ===
        with col_work:
            
            # 1. Metadata Section (Always Visible)
            with st.expander("🏷️ Metadata (Frontmatter)", expanded=True):
                c1, c2 = st.columns([2, 1])
                doi_val = c1.text_input("DOI", value=data["doi_data"].get("doi") or "N/A")
                
                citation_val = st.text_area(
                    "Citation (APA)", 
                    value=data["ai_metadata"].get("citation", ""),
                    height=70
                )
                
                kw_raw = data["ai_metadata"].get("keywords", [])
                if isinstance(kw_raw, list):
                    kw_raw = ", ".join(kw_raw)
                keywords_val = st.text_input("Keywords", value=kw_raw)
                
                summary_val = st.text_area(
                    "Executive Summary", 
                    value=data["ai_metadata"].get("summary", ""),
                    height=100
                )

            # 2. Tabs for Edit vs Preview
            tab_edit, tab_preview = st.tabs(["✏️ Raw Editor", "👁️ Rendered Preview"])
            
            with tab_edit:
                st.caption("Edit the raw Markdown here. Fix tables or image links.")
                # We use session_state.editor_markdown to bind the value
                text_content = st.text_area(
                    "Markdown Content", 
                    value=st.session_state.editor_markdown, 
                    height=600,
                    label_visibility="collapsed",
                    key="editor_markdown"
                )

            with tab_preview:
                st.caption("Verify how tables and headers render.")
                st.markdown("---")
                # This renders whatever is currently in the text area
                st.markdown(st.session_state.editor_markdown)
                st.markdown("---")
                
                # Image Preview Grid inside Preview Tab
                assets_path = Path(data["temp_path"]) / "assets"
                if assets_path.exists():
                    images = list(assets_path.glob("*.png"))
                    if images:
                        st.markdown(f"**Attached Assets ({len(images)})**")
                        img_cols = st.columns(3)
                        for i, img in enumerate(images):
                            with img_cols[i % 3]:
                                st.image(str(img), caption=img.name, use_container_width=True)

            # 3. Save Action (Bottom)
            st.markdown("---")
            if st.button("💾 Save to Library", type="primary", use_container_width=True):
                try:
                    final_base = Path("data/processed") / data["stem"]
                    ensure_directory(final_base)
                    ensure_directory(final_base / "assets")

                    final_metadata = {
                        "filename": data["filename"],
                        "processed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "doi": doi_val,
                        "citation": citation_val,
                        "summary": summary_val,
                        "keywords": keywords_val
                    }

                    # Use the content from session state (latest edits)
                    save_markdown_with_frontmatter(
                        final_base / f"{data['stem']}.md",
                        st.session_state.editor_markdown, 
                        final_metadata
                    )

                    assets_path = Path(data["temp_path"]) / "assets"
                    if assets_path.exists():
                        for img in assets_path.glob("*"):
                            shutil.copy2(img, final_base / "assets" / img.name)

                    st.success(f"Saved to {final_base}!")
                    time.sleep(1.5)
                    reset_session()
                    st.rerun()

                except Exception as e:
                    st.error(f"Save failed: {e}")

if __name__ == "__main__":
    main()