import os
from groq import Groq

client = None


def _get_llm_client():
    global client
    if client is not None:
        return client

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set. Set the environment variable before using LLM features.")

    client = Groq(api_key=api_key)
    return client


def call_llm(prompt, temperature=0.7):
    try:
        client = _get_llm_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"LLM_ERROR: {str(e)}"