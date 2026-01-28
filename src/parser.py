import shutil
from pathlib import Path
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

class RAGParser:
    def __init__(self):
        # Configure pipeline options
        self.pipeline_options = PdfPipelineOptions()
        self.pipeline_options.do_ocr = True
        self.pipeline_options.do_table_structure = True
        self.pipeline_options.table_structure_options.do_cell_matching = True
        
        # Ensure images are extracted
        self.pipeline_options.generate_picture_images = True

        self.format_options = {
            InputFormat.PDF: PdfFormatOption(pipeline_options=self.pipeline_options)
        }

        self.converter = DocumentConverter(format_options=self.format_options)

    def process_pdf(self, input_path: Path, output_dir: Path) -> str:
        """
        Converts PDF to Markdown, extracting images to an assets folder.
        """
        assets_dir = output_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)

        print(f"Parsing PDF: {input_path.name}...")
        
        # 1. Convert the document
        conversion_result = self.converter.convert(input_path)
        
        # 2. Extract and save images manually to ensure naming control
        # We iterate and save them as image_1.png, image_2.png, etc.
        image_map = {}
        
        for i, picture in enumerate(conversion_result.document.pictures):
            image = picture.get_image(conversion_result.document)
            if image:
                filename = f"image_{i+1}.png"
                image_path = assets_dir / filename
                image.save(image_path)
                # Map the internal docling reference to our new filename if needed
                # (Docling default export might need regex replacement if we want perfect control,
                # but standard export usually references them sequentially. 
                # For strict RAG, we accept the standard export text here.)

        # 3. Export to Markdown
        # This returns the text. Docling inserts placeholders like or standard MD images.
        markdown_content = conversion_result.document.export_to_markdown()
        
        return markdown_content