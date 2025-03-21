import os
import asyncio
from pyrogram import Client, filters
from pymongo import MongoClient
from pyrogram.types import Message
import multiprocessing
import uvicorn
from fastapi import FastAPI

# Set up bot and MongoDB credentials
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
MONGODB_URI = os.getenv("MONGODB_URI")

# Initialize bot and MongoDB
bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
mongo_client = MongoClient(MONGODB_URI)
db = mongo_client["telegram_bot_db"]
users_collection = db["users"]

# FastAPI for health check
app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Function to add a user to MongoDB if new
async def add_user(user_id, username=None, first_name=None, last_name=None):
    # Check if user already exists
    user_data = users_collection.find_one({"user_id": user_id})
    if not user_data:
        # Insert new user into DB
        users_collection.insert_one({
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name
        })
    else:
        print(f"User {user_id} already exists in the database")

# Command to get user count
@bot.on_message(filters.command("users") & filters.user(ADMIN_ID))
async def user_count_command(_, message: Message):
    user_count = users_collection.count_documents({})
    await message.reply(f"Total users: {user_count}")

# Command to broadcast a message to all users
@bot.on_message(filters.command("broadcast") & filters.user(ADMIN_ID) & filters.reply)
async def broadcast_command(_, message: Message):
    broadcast_message = message.reply_to_message.text
    user_ids = [user["user_id"] for user in users_collection.find()]
    
    for user_id in user_ids:
        try:
            await bot.send_message(chat_id=user_id, text=broadcast_message)
        except Exception as e:
            print(f"Could not send message to {user_id}: {e}")

    await message.reply("Broadcast sent to all users.")

# Track unique users
@bot.on_message(filters.private)
async def track_user(_, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    # Add or update user in the database
    await add_user(user_id, username, first_name, last_name)

# Ignore other commands
@bot.on_message(~filters.command(["users", "broadcast"]))
async def ignore_other_commands(_, message: Message):
    if message.from_user.id == ADMIN_ID:
        return

# Function to start FastAPI in a separate process
def start_fastapi():
    # Run the FastAPI app on port 8080
    uvicorn.run("bot:app", host="0.0.0.0", port=8080)

# Function to start the bot
def start_bot():
    bot.run()

if __name__ == "__main__":
    # Start FastAPI in a separate process
    fastapi_process = multiprocessing.Process(target=start_fastapi)
    fastapi_process.start()

    # Start the bot in the main process
    start_bot()
