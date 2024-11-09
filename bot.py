from pyrogram import Client, filters
from pyrogram.types import Message

# Replace with your own credentials
API_ID = "YOUR_API_ID"
API_HASH = "YOUR_API_HASH"
BOT_TOKEN = "YOUR_BOT_TOKEN"
OWNER_ID = 6057768840  # Replace with your Telegram user ID

# Initialize the bot
bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Restrict command access to the owner only
def owner_only(func):
    async def wrapper(client, message: Message):
        if message.from_user and message.from_user.id == OWNER_ID:
            await func(client, message)
        else:
            await message.reply("You are not authorized to use this command.")
    return wrapper

# /users command - count and return the number of users in the bot
@bot.on_message(filters.command("users") & filters.user(OWNER_ID))
@owner_only
async def user_count(client, message: Message):
    users_count = await bot.get_chat_members_count(message.chat.id)
    await message.reply(f"Total users in this chat: {users_count}")

# /broadcast command - send a broadcast to all users in the chat
@bot.on_message(filters.command("broadcast") & filters.user(OWNER_ID) & filters.reply)
@owner_only
async def broadcast_message(client, message: Message):
    text = message.reply_to_message.text
    async for member in bot.iter_chat_members(message.chat.id):
        try:
            await bot.send_message(member.user.id, text)
        except Exception as e:
            print(f"Could not send message to {member.user.id}: {e}")
    await message.reply("Broadcast sent to all users.")

# Filter other messages - make bot unresponsive to /start or other commands
@bot.on_message(filters.command(["start", "help", "info"]) & ~filters.user(OWNER_ID))
async def ignore_other_commands(client, message: Message):
    pass  # Do nothing, silently ignore these commands

print("Bot is running...")
bot.run()
