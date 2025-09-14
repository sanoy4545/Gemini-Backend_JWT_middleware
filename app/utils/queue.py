import asyncio
import json
from app.core.redis_client import redis_client

QUEUE_NAME = "gemini_message_queue"

async def enqueue_gemini_task(chatroom_id: int, user_id: int, message_id: int, content: str):
    task = {
        "chatroom_id": chatroom_id,
        "user_id": user_id,
        "message_id": message_id,
        "content": content
    }
    await redis_client.rpush(QUEUE_NAME, json.dumps(task))

# You would have a separate worker process that pops from this queue and calls Gemini API asynchronously.
