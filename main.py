from fastapi import FastAPI
import aioredis
import uuid
from openai_chatbot import get_message_response
import os
from dotenv import load_dotenv
import uvicorn

load_dotenv()

app = FastAPI()

redis = aioredis.from_url('redis://default:u7D2rM07iGHwxqZV6hbX@containers-us-west-92.railway.app:6693', decode_responses=True)

async def clear_redis():
    try:
        await redis.execute_command(
                'FLUSHDB',
            )
    except Exception as e:
        print(e)
    
    try:
        await redis.execute_command(
                'FLUSHALL',
            )
    except Exception as e:
        print(e)
    

@app.on_event('startup')
async def startup_event():
    await clear_redis()
    print ("Redis cleared")


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/create-session")
async def create_session(base_prompt: str = "You are a friendly chatbot", secret_key: str = "secret"):
    # Generates a random session id as a hash, creates a key in redis with the session id
    # and returns the session id to the user

    # Check if the secret key is correct
    if secret_key != os.getenv('SECRET_KEY'):
        return {"error": "Invalid secret key"}

    session_id = uuid.uuid4().hex

    await redis.set(f"{session_id}:base_prompt", base_prompt)
    await redis.expire(f"{session_id}:base_prompt", 60*60)
    await redis.lpush(f"{session_id}:user", 'Start')
    await redis.expire(f"{session_id}:user", 60*60)
    await redis.lpush(f"{session_id}:bot", 'Start')
    await redis.expire(f"{session_id}:bot", 60*60)

    return {"session_id": session_id}

@app.get("/get-session")
async def get_session(session_id: str, secret_key: str = "secret"):
    # Gets the session from redis and returns it to the user

     # Check if the secret key is correct
    if secret_key != os.getenv('SECRET_KEY'):
        return {"error": "Invalid secret key"}

    try:
        base_prompt = await redis.get(f'{session_id}:base_prompt')
        return {"status": "open"}
    except Exception as e:
        print(e)
        return {"status": "ended"}

@app.get("/message")
async def message(session_id: str, message: str, secret_key: str = "secret"):
    # Get the base prompt from redis

     # Check if the secret key is correct
    if secret_key != os.getenv('SECRET_KEY'):
        return {"error": "Invalid secret key"}

    try:
        base_prompt = await redis.get(f'{session_id}:base_prompt')
    except Exception as e:
        print(e)
        return {"error": "Session not found"}
    
    if base_prompt is None:
        return {"error": "Session not found"}
    
    # Get openai key from .env file

    key = os.getenv('OPENAI_KEY')

    # Get the bot and user messages from redis, excluding the start message
    user_messages = await redis.lrange(f"{session_id}:user", 1, -1)
    bot_messages = await redis.lrange(f"{session_id}:bot", 1, -1)

    # Generate the prompt for the chatbot
    response = get_message_response(user_messages, bot_messages, message, base_prompt, key)
    await redis.rpush(f"{session_id}:bot", response)
    await redis.rpush(f"{session_id}:user", message)

    return {"response": response}


@app.get("/get-conversation")
async def get_conversation(session_id: str, secret_key: str = "secret"):
     # Check if the secret key is correct
    if secret_key != os.getenv('SECRET_KEY'):
        return {"error": "Invalid secret key"}
    # Get the bot and user messages from redis, excluding the start message
    user_messages = await redis.lrange(f"{session_id}:user", 1, -1)
    bot_messages = await redis.lrange(f"{session_id}:bot", 1, -1)

    return {"user_messages": user_messages, "bot_messages": bot_messages}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=os.getenv("PORT", default=5000), log_level="info")