import os
import httpx
import pandas as pd
from dotenv import load_dotenv

load_dotenv()                         # backend/.env
load_dotenv(dotenv_path="../.env")    # project root .env

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

SYSTEM_PROMPT = """You are a data analysis assistant. You receive metadata about a pandas DataFrame and a user question.
Your job is to generate Python/pandas code that answers the question.

Rules:
- The DataFrame is available as `df`.
- pandas is imported as `pd`, numpy as `np`, matplotlib.pyplot as `plt`, seaborn as `sns`.
- Store the final answer in a variable called `result`.
- If the question asks for a chart/plot/graph/visualization, generate matplotlib or seaborn code to create it. Do NOT set `result` for chart-only answers.
- For charts: always add axis labels and a title.
- Only output Python code — no explanations, no markdown fences.
- Do NOT import any modules.
- Do NOT use open(), os, subprocess, or __import__.
- Do NOT access the file system or network.
- Keep the code concise and correct."""


def build_prompt(df: pd.DataFrame, question: str) -> str:
    col_info = []
    for col in df.columns:
        col_info.append(f"  - {col} ({df[col].dtype})")

    sample = df.head(5).to_string(index=False)

    return (
        f"DataFrame info:\n"
        f"- Shape: {df.shape[0]} rows x {df.shape[1]} columns\n"
        f"- Columns:\n" + "\n".join(col_info) + "\n\n"
        f"Sample rows:\n{sample}\n\n"
        f"Question: {question}"
    )


async def ask_openai(df: pd.DataFrame, question: str) -> str:
    """Send a question to OpenAI and return the generated code."""
    user_prompt = build_prompt(df, question)

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            OPENAI_URL,
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0,
                "max_tokens": 1024,
            },
        )
        response.raise_for_status()
        data = response.json()

    code = data["choices"][0]["message"]["content"].strip()
    # Strip markdown fences if the model wraps the code
    if code.startswith("```"):
        lines = code.split("\n")
        lines = lines[1:]  # remove opening fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        code = "\n".join(lines)

    return code
