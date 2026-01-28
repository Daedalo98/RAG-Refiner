import ollama
from typing import Dict, Any

class ContentEnricher:
    def __init__(self, model: str = "granite4:7b-a1b-h"):
        self.model = model

    def enrich_content(self, markdown_text: str) -> Dict[str, Any]:
        """
        Sends a truncated version of the text to Ollama to generate metadata.
        """
        # Truncate text to avoid context window overflow (approx first 10k chars usually enough for summary)
        context_text = markdown_text[:12000]

        prompt = f"""
        Analyze the following technical document content:

        {context_text}

        ---
        Task:
        1. Generate a list of 5-8 technical keywords.
        2. Create a clean, APA-style citation string for this document based on the text (guess the title/author if not explicit).
        3. Write a 2-sentence executive summary.

        Output strictly in JSON format with keys: "keywords" (list), "citation" (string), "summary" (string).
        """

        try:
            print("Querying Local Ollama (this may take a moment)...")
            response = ollama.chat(model=self.model, messages=[
                {
                    'role': 'user',
                    'content': prompt,
                },
            ], format='json')
            
            # extract content
            result_json = response['message']['content']
            
            # Simple parsing wrapper (ollama python lib returns dict for format='json' often, but sometimes string)
            import json
            if isinstance(result_json, str):
                return json.loads(result_json)
            return result_json

        except Exception as e:
            print(f"Enrichment failed: {e}")
            return {
                "keywords": [],
                "citation": "Error generating citation",
                "summary": "Error generating summary"
            }