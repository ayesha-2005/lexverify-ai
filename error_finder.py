import os
from dotenv import load_dotenv
from openai import OpenAI
from src.orchestrator import run_lexverify_pipeline

load_dotenv()
client = OpenAI(
    base_url='https://api.groq.com/openai/v1',
    api_key=os.getenv('GROQ_API_KEY')
)
res = run_lexverify_pipeline('Can pre-arrest bail be granted where mala fide is alleged?', client)
print('\n--- EXACT ERRORS ---')
print(res['errors'])