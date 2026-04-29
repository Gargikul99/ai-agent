from google import genai
from google.genai import types

client = genai.Client(api_key="AIzaSyCUsmYY3Pk_RuMQNl16zR2P8t_8SMOPkZo")

response = client.models.generate_content(
    model="models/gemini-2.0-flash-lite",
    contents=[{"role": "user", "parts": [{"text": "Say hello"}]}]
)

print(response.text)