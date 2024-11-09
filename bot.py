import os
from pyrogram import Client, filters
from pymongo import MongoClient
from pyrogram.types import Message
from fastapi import FastAPI
import uvicorn
from threading import Thread

# Set up your bot and MongoDB credentials
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
MONGODB_URI = os.getenv("MONGODB_URI")

# Initialize the bot and MongoDB client
bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
mongo_client = MongoClient(MONGODB_URI)
db = mongo_client["telegram_bot_db"]
users_collection = db["users"]

# FastAPI for health check
app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Function to add a user to MongoDB if they are new
async def add_user(user_id):
    if not users_collection.find_one({"user_id": user_id}):
        users_collection.insert_one({"user_id": user_id})

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

# Track unique users who interact with the bot
@bot.on_message(filters.private)
async def track_user(_, message: Message):
    user_id = message.from_user.id
    await add_user(user_id)

# Ignore other commands except for admin commands defined above
@bot.on_message(~filters.command(["users", "broadcast"]))
async def ignore_other_commands(_, message: Message):
    if message.from_user.id == ADMIN_ID:
        return

# Function to run the FastAPI app in a separate thread
def run_health_check_server():
    uvicorn.run("bot:app", host="0.0.0.0", port=8080)

if __name__ == "__main__":
    # Start the health check server in a separate thread
    Thread(target=run_health_check_server).start()
    print("Bot is running...")
    bot.run()
