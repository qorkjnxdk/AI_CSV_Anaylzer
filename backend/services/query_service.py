import os
import json
import logging
import httpx
import pandas as pd
from dotenv import load_dotenv

logger = logging.getLogger("uvicorn.error")

load_dotenv()                         # backend/.env
load_dotenv(dotenv_path="../.env")    # project root .env

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

SYSTEM_PROMPT = """You are a data analysis assistant. Given a pandas DataFrame and a user question, return JSON: {"type": "code" or "string", "result": <value>}.

- "code": Python code that computes the answer using `df`.
- "string": A plain-text answer (for explanations or non-computational questions).

Available variables: `df` (DataFrame), `pd`, `np`, `plt`, `sns`.

Output variables (all optional, combine as needed):
- `result`: a short descriptive string summarizing the answer (e.g. `result = "Main divisions and their project counts:"`).
- `result_table`: a DataFrame or Series with the tabular data. The system renders this as a formatted table automatically.
- Charts: any matplotlib/seaborn plot is captured automatically.
- When the answer involves tabular data, ALWAYS split it: set `result` to a descriptive label and `result_table` to the DataFrame/Series. NEVER concatenate a DataFrame into a string with `.to_string()`.

Example:
```
counts = df.groupby('Division').size()
result = "Number of projects per division:"
result_table = counts
```
- For charts: add titles, axis labels, use `plt.tight_layout()`, and annotate bars when < 10 categories.
- Do NOT import modules, access the filesystem, or use `open()`, `os`, `subprocess`."""


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


async def ask_openai(df: pd.DataFrame, question: str) -> dict:
    """Send a question to OpenAI and return generated code or a text response.

    Returns a dict with:
        - type: "code" | "text"
        - data: the content string
    """
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

    # Check for refusal in the API response
    refusal = data["choices"][0]["message"].get("refusal")
    if refusal:
        return {"type": "text", "data": refusal}

    content = data["choices"][0]["message"]["content"].strip()
    logger.info("[LLM raw response]\n%s", content)
    # Strip markdown fences if the model wraps the response
    if content.startswith("```"):
        lines = content.split("\n")
        lines = lines[1:]  # remove opening fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines)

    # Parse the structured JSON response from the LLM
    try:
        parsed = json.loads(content)
        resp_type = parsed.get("type", "")
        result = parsed.get("result", "")

        if resp_type == "string":
            return {"type": "text", "data": result}
        if resp_type == "code":
            return {"type": "code", "data": result}
    except (json.JSONDecodeError, AttributeError):
        pass

    # Fallback: if not valid JSON, try to detect code vs text
    try:
        compile(content, "<generated>", "exec")
    except SyntaxError:
        return {"type": "text", "data": content}

    return {"type": "code", "data": content}
