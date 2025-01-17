import vertexai
from vertexai.preview.generative_models import GenerativeModel, Image

PROJECT_ID = "gen-ai-441105"
REGION = "us-central1"
vertexai.init(project=PROJECT_ID, location=REGION)

IMAGE_FILE = "/Users/jordynkim/Library/CloudStorage/OneDrive-ColbyCollege/Design For Generative AI/gpt_dalle_demo_fall24/static/uploads/Screenshot_2024-11-08_at_12.44.01_AM.png"
image = Image.load_from_file(IMAGE_FILE)

generative_multimodal_model = GenerativeModel("gemini-1.5-flash-002")
response = generative_multimodal_model.generate_content(["Identify the main clothing item in this image.", image])

print(response)