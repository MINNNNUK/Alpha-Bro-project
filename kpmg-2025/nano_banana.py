from google import genai

client = genai.Client(api_key="AIzaSyAMGdoALEjDLi0FLW-RmKQoFpaz3G6OTp8")

response = client.models.generate_content(
    model="gemini-2.5-flash", contents="Explain how AI works in a few words"
)
print(response.text)

from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO

client = genai.Client(api_key="AIzaSyBd6eIxnqNCWhPJzbN1cHhoE-NQ5WUd0hI")


prompt = (
    " korean kpmg company future academy students for IT, no text, casual style, 20's ~30's stydents no worker"
)

response = client.models.generate_content(
    model="gemini-2.5-flash-image-preview",
    contents=[prompt],
)

for part in response.candidates[0].content.parts:
    if part.text is not None:
        print(part.text)
    elif part.inline_data is not None:
        image = Image.open(BytesIO(part.inline_data.data))
        image.save("generated_image.png")
