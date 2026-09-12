import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(
    base_url='https://api.groq.com/openai/v1',
    api_key=os.getenv('GROQ_API_KEY')
)

res = client.chat.completions.create(
    model='llama-3.3-70b-versatile',
    messages=[{'role': 'user', 'content': 'Hello'}]
)
print('API Connection Successful:', res.choices[0].message.content)