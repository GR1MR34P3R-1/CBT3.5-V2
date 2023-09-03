import discord
from discord.ext import commands
import configparser
import openai
import asyncio
import sqlite3
import pytz
from datetime import datetime
import logging
import sys
import signal

# Custom exceptions
class BotInitializationError(Exception):
    pass

class DatabaseError(Exception):
    pass

class OpenAIError(Exception):
    pass

class DiscordError(Exception):
    pass

class RateLimitError(Exception):
    pass

# Centralized logging
logging.basicConfig(level=logging.INFO)
bot_logger = logging.getLogger('bot')
db_logger = logging.getLogger('database')
openai_logger = logging.getLogger('openai')

# Configure log levels
db_logger.setLevel(logging.ERROR)
openai_logger.setLevel(logging.ERROR)

file_handler = logging.FileHandler('bot.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

bot_logger.addHandler(file_handler)
db_logger.addHandler(file_handler)
openai_logger.addHandler(file_handler)

# Signal handler for graceful shutdown
def signal_handler(sig, frame):
    bot_logger.info("Received termination signal. Shutting down...")
    db_connection.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Read config.ini
config = configparser.ConfigParser()
config.read('config.ini')

token = config['Bot']['token']
api_key = config['Bot']['api_key']
cleanup_duration = int(config['Bot']['cleanup_duration'])

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Initialize the OpenAI API
try:
    openai.api_key = api_key
except openai.error.OpenAIError as openai_error:
    openai_logger.error(f"OpenAI API initialization error: {str(openai_error)}")
    raise OpenAIError("OpenAI API initialization failed.") from openai_error

# Create a connection to the database
try:
    db_connection = sqlite3.connect('database.db')
except sqlite3.Error as db_error:
    db_logger.error(f"Database connection error: {str(db_error)}")
    raise DatabaseError("Database connection failed.") from db_error

# Create a cursor object to execute SQL queries
db_cursor = db_connection.cursor()

# Create the tables if they don't exist
try:
    db_cursor.execute('''
        CREATE TABLE IF NOT EXISTS channel_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id INTEGER,
            channel_name TEXT,
            guild_id INTEGER,
            guild_name TEXT,
            author_id INTEGER,
            author_name TEXT,
            content TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    db_cursor.execute('''
        CREATE TABLE IF NOT EXISTS command_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER,
            guild_name TEXT,
            channel_id INTEGER,
            channel_name TEXT,
            author_id INTEGER,
            author_name TEXT,
            command TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    db_connection.commit()
except sqlite3.Error as db_error:
    db_logger.error(f"Database table creation error: {str(db_error)}")
    raise DatabaseError("Database table creation failed.") from db_error

# Define a dictionary to cache generated responses
response_cache = {}

# Function to generate a response using ChatGPT 3.5 Turbo
async def generate_response(user_message, bot_user, bot_channel):
    model_prompt = f"User: {user_message.content}\nAI: "
    cache_key = model_prompt + str(user_message.author.id)

    if cache_key in response_cache:
        generated_text = response_cache[cache_key]
    else:
        try:
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=model_prompt,
                max_tokens=100,
                temperature=0.7,
                n=1,
                stop=None,
                user=str(user_message.author.id),
            )
            generated_text = response.choices[0].text.strip()

            response_cache[cache_key] = generated_text
        except openai.error.OpenAIError as openai_error:
            openai_logger.error(f"OpenAI API error: {str(openai_error)}")
            raise OpenAIError("OpenAI API error occurred.") from openai_error

    bot_response = generated_text + ' AI: '

    # Log bot response
    log_message(bot_user, bot_channel, bot_response)

    return bot_response

# Function to log messages to the database and export logs to a text file
def log_message(author, channel, content):
    author_id = author.id
    author_name = author.name

    if author == bot.user:
        author_id = bot.user.id
        author_name = bot.user.name

    timestamp = datetime.now(pytz.timezone('America/Phoenix'))

    try:
        db_cursor.execute(
            '''
            INSERT INTO channel_logs (
                channel_id, channel_name, guild_id, guild_name,
                author_id, author_name, content, timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            channel.id, channel.name,
            channel.guild.id, channel.guild.name,
            author_id, author_name,
            content, timestamp
        ))

        # Commit the changes to the database
        db_connection.commit()

        # Export logs to a text file
        export_logs()
    except sqlite3.Error as db_error:
        db_logger.error(f"Database logging error: {str(db_error)}")
        raise DatabaseError("Database logging failed.") from db_error

# Function to export logs to a text file
def export_logs():
    db_cursor.execute('SELECT * FROM channel_logs')
    channel_logs = db_cursor.fetchall()
    with open('loggeddata.txt', 'w', encoding='utf-8') as file:
        file.write('Channel Logs:\n\n')
        for log in channel_logs:
            timestamp_str = log[8]
            timestamp = datetime.fromisoformat(timestamp_str)
            local_timestamp = timestamp.astimezone(pytz.timezone('America/Phoenix'))

            file.write(f'ID: {log[0]}\n')
            file.write(f'Channel: {log[2]} ({log[1]})\n')
            file.write(f'Guild: {log[4]} ({log[3]})\n')
            file.write(f'Author: {log[6]} ({log[5]})\n')
            file.write(f'Content: {log[7]}\n')
            file.write(f'Timestamp: {local_timestamp}\n\n')

    db_cursor.execute('SELECT * FROM command_logs')
    command_logs = db_cursor.fetchall()
    with open('loggeddata.txt', 'a', encoding='utf-8') as file:
        file.write('\n\nCommand Logs:\n\n')
        for log in command_logs:
            timestamp_str = log[8]
            timestamp = datetime.fromisoformat(timestamp_str)
            local_timestamp = timestamp.astimezone(pytz.timezone('America/Phoenix'))

            file.write(f'ID: {log[0]}\n')
            file.write(f'Guild: {log[2]} ({log[1]})\n')
            file.write(f'Channel: {log[4]} ({log[3]})\n')
            file.write(f'Author: {log[6]} ({log[5]})\n')
            file.write(f'Command: {log[7]}\n')
            file.write(f'Timestamp: {local_timestamp}\n\n')

# Event handler for the on_message event
@bot.event
async def on_message(message):
    if message.author == bot.user:
        await asyncio.sleep(120)
        try:
            await message.delete()
        except discord.errors.NotFound:
            pass
        return

    log_message(message.author, message.channel, message.content)

    if message.channel.name == "ask-anything":
        special_access_role = discord.utils.get(message.guild.roles, name="Special Access")
        verified_role = discord.utils.get(message.guild.roles, name="Verified")

        if special_access_role in message.author.roles and verified_role in message.author.roles:
            try:
                response = await generate_response(message, bot.user, message.channel)
                await message.channel.send(response)

                # Log bot response (handled in generate_response)

                # Delete user question after 1 minute
                await asyncio.sleep(60)
                try:
                    await message.delete()
                except discord.errors.NotFound:
                    pass

                # Delete bot response after 2 minutes
                await asyncio.sleep(120)
                async for msg in message.channel.history(limit=200):
                    if (
                        msg.author == bot.user
                        and msg.reference is not None
                        and msg.reference.message_id == message.id
                    ):
                        try:
                            await msg.delete()
                        except discord.errors.NotFound:
                            pass
                        break
            except RateLimitError as rate_limit_error:
                bot_logger.warning(f"Rate limit exceeded: {str(rate_limit_error)}")
                # Implement retry logic or backoff strategies
            except DiscordError as discord_error:
                bot_logger.error(f"Discord error: {str(discord_error)}")
                await message.channel.send(f"Discord error: {str(discord_error)}")
            except Exception as e:
                # Handle other errors
                error_message = f"An error occurred: {str(e)}"
                bot_logger.error(error_message)
                await message.channel.send(error_message)
        elif verified_role in message.author.roles:
            # User has only "Verified" role
            # Delete user message instantly
            try:
                await message.delete()
            except discord.errors.NotFound:
                pass

            # Log access denial in the channel_logs table
            log_message(bot.user, message.channel, "You do not have the required role for special access.")

            # Send access denial message if not already sent
            error_sent = False
            async for msg in message.channel.history(limit=10):
                if (
                    msg.author == bot.user
                    and msg.content == "You do not have the required role for special access."
                ):
                    error_sent = True
                    break
            if not error_sent:
                await message.channel.send("You do not have the required role for special access.")
        else:
            # Log access denial in the channel_logs table
            log_message(bot.user, message.channel, "You do not have the required role for special access.")

            # Send access denial message if not already sent
            error_sent = False
            async for msg in message.channel.history(limit=10):
                if (
                    msg.author == bot.user
                    and msg.content == "You do not have the required role for special access."
                ):
                    error_sent = True
                    break
            if not error_sent:
                await message.channel.send("You do not have the required role for special access.")

    await bot.process_commands(message)

# Event handler for the on_command event
@bot.event
async def on_command(ctx):
    try:
        db_cursor.execute(
            '''
            INSERT INTO command_logs (
                guild_id, guild_name, channel_id, channel_name,
                author_id, author_name, command
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''',
            (
                ctx.guild.id, ctx.guild.name,
                ctx.channel.id, ctx.channel.name,
                ctx.author.id, ctx.author.name,
                ctx.message.content,
            ),
        )

        # Commit the changes to the database
        db_connection.commit()
    except sqlite3.Error as db_error:
        db_logger.error(f"Database command logging error: {str(db_error)}")
        raise DatabaseError("Database command logging failed.") from db_error

# Event handler for the on_ready event
@bot.event
async def on_ready():
    print(f'Bot is ready. Connected to {len(bot.guilds)} server(s).')

    while True:
        await asyncio.sleep(cleanup_duration * 60)
        await cleanup_channels()

# Event handler for the on_command_error event
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing required argument.")
    elif isinstance(error, openai.error.OpenAIError):
        await ctx.send(f"OpenAI API error: {str(error)}")
    else:
        error_message = f"An error occurred: {str(error)}"
        bot_logger.error(error_message)
        await ctx.send("An error occurred while processing the command.")

# Cleanup function to delete all messages from non "ask-anything" text channels
async def cleanup_channels():
    for guild in bot.guilds:
        for channel in guild.text_channels:
            if channel.name != "ask-anything":
                async for message in channel.history(limit=None):
                    try:
                        await message.delete()
                    except discord.errors.NotFound:
                        pass

# Start the bot
try:
    bot.run(token)
except Exception as e:
    bot_logger.error(f"An error occurred during bot execution: {str(e)}")
    db_connection.close()
    sys.exit(1)
