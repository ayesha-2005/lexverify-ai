import os
from dotenv import load_dotenv
from openai import OpenAI
from src.orchestrator import run_lexverify_pipeline

load_dotenv()

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY")
)

question = "Can pre-arrest bail be granted where mala fide is alleged under Pakistani law?"
print(f"Running pipeline for: '{question}'...\n")

final_state = run_lexverify_pipeline(question, client)

print("=== FINAL ANSWER ===")
print(final_state["final_answer"])
print("\n=== VERIFIED CITATIONS ===")
print([c["citation"] for c in final_state.get("verified_citations", [])])
print("\n=== REJECTED CITATIONS ===")
print(final_state.get("rejected_citations", []))
print("\n=== PIPELINE STATUS ===")
print(final_state["status"])