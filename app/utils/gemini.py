from google import genai
import os
import httpx

# The client gets the API key from the environment variable `GEMINI_API_KEY`.
client = genai.Client()

async def send_to_gemini(messages: list[dict]) -> str:
    """
    messages: list of dicts, e.g. [{"role": "user", "content": "Hello"}, ...]
    Returns: Gemini's response text
    """
    # Compose the conversation as a single string (simple version)
    conversation = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
    # Call Gemini API (sync call, so run in thread pool for async)
    import asyncio
    loop = asyncio.get_event_loop()
    def call_gemini():
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=conversation
        )
        return response.text
    return await loop.run_in_executor(None, call_gemini)
