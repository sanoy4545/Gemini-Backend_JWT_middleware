import asyncio
import json
from app.core.redis_client import redis_client
from app.utils.gemini import send_to_gemini
from app.models.message import Message
from app.core.database import AsyncSessionLocal
from sqlalchemy import select
from app.models.chatroom import Chatroom
from app.models.user import User

async def gemini_worker():
    print("Gemini worker started...")
    while True:
        task_json = await redis_client.lpop("gemini_message_queue")
        if not task_json:
            await asyncio.sleep(1)
            continue
        task = json.loads(task_json)
        chatroom_id = task["chatroom_id"]
        user_id = task["user_id"]
        message_id = task["message_id"]
        content = task["content"]
        # Build conversation history (optional: fetch last N messages)
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Message).where(Message.chatroom_id == chatroom_id).order_by(Message.created_at.desc()))
            all_msgs = result.scalars().all()
            # Only use the last user message as context
            last_user_msg = next((m for m in all_msgs if m.sender == "user"), None)
            if last_user_msg:
                history = [{"role": "user", "content": last_user_msg.content}]
            else:
                history = []
        # Send to Gemini
        try:
            gemini_response = await send_to_gemini(history)
        except Exception as e:
            print(f"Gemini API error: {e}")
            gemini_response = "[Gemini API error: could not get response]"
        # Save Gemini response to DB
        async with AsyncSessionLocal() as db:
            ai_message = Message(chatroom_id=chatroom_id, sender="ai", content=gemini_response)
            db.add(ai_message)
            await db.commit()
        print(f"Gemini response saved for chatroom {chatroom_id}")

if __name__ == "__main__":
    asyncio.run(gemini_worker())
