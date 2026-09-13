import os
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
from src.orchestrator import run_lexverify_pipeline

load_dotenv()

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY")
)
