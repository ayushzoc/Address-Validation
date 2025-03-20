from vertexai.generative_models import GenerationConfig
from vertexai.preview.generative_models import GenerativeModel, Part
from google.cloud import storage
from rolls_lease_matcher.utility import clean_json_strings


class Extractor:
    def __init__(self, bucket_name: str, system_prompt: str):
        self.generation_config = GenerationConfig(temperature = 0, top_p = 0.2)
        self.extraction_llm = GenerativeModel(model_name = "gemini-1.5-flash-001", system_instruction = [system_prompt])
        self.client = storage.Client()
        self.bucket = self.client.get_bucket(bucket_name)
        
    def extract(self, gcs_folder: str, extraction_prompt: str, ext = ".pdf", mime_type = "application/pdf"):
        response_list = []
        blobs = self.bucket.list_blobs(prefix = gcs_folder)
        for blob in blobs:
            print(f"Extractor processing for : {blob}")
            if blob.name.endswith('.csv'):
                mime_type = "text/csv"
            pdf_uri = f"gs://{self.bucket.name}/{blob.name}"
            pdf_file = Part.from_uri(uri = pdf_uri, mime_type = mime_type)
            contents = [pdf_file, extraction_prompt]
            response = self.extraction_llm.generate_content(contents, generation_config = self.generation_config)
            response = clean_json_strings(response.text)
            response_list.append({blob.name:response})
            print(f"Processed {blob.name}")
        return response_list