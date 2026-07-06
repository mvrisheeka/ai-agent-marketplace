import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

def call_llm(prompt: str):
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        })

        data = response.json()
        return data.get("response", "No response")

    except Exception as e:
        return f"LLM Error: {str(e)}"