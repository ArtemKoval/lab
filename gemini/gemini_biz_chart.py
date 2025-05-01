import os
import google.generativeai as genai
from PIL import Image

# Set your Google API key securely via environment variable
os.environ["GOOGLE_API_KEY"] = "your-api-key-here"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

# Define image path (update this to your chart image)
image_path = "path/to/your/business_chart.png"

# Load the image
try:
    image = Image.open(image_path)
except FileNotFoundError:
    raise SystemExit("Image file not found. Please verify the image path.")

# Initialize Gemini Pro Vision model
model = genai.GenerativeModel("gemini-pro-vision")

# Define analysis prompt (customize based on your needs)
prompt = """
Analyze this business chart and provide insights on:
- Key metrics shown
- Trends observed
- Any anomalies or notable patterns
- Possible business implications
"""

# Generate analysis from model
try:
    response = model.generate_content([prompt, image])
    print("\nGemini Vision Analysis Result:")
    print("------------------------------")
    print(response.text)
except Exception as e:
    print(f"Error generating analysis: {e}")