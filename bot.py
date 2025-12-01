bot.py
import os
import discord
import asyncio
import requests
from discord.ext import commands
from flask import Flask
import threading

# -------------------- KEEP BOT ALIVE --------------------
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = threading.Thread(target=run_flask)
    t.start()

keep_alive()

# -------------------- CONFIG --------------------
TOKEN = os.environ.get("MTQ0NTEwNDExNDA3NzAxMjE0MA.GJ7MA2.64nUmO6kMrDuM23yFKLv2HlpjGmN-AGuEV8Tm0")  # Add this in Railway/Replit environment
CHANNEL_ID = int(os.environ.get("1444439009978745012", 0))  # Optional env var
ROLE_ID = int(os.environ.get("1445118334088642652", 0)) if os.environ.get("ROLE_ID") else None
ROLE_NAME = os.environ.get("ROLE_NAME", "Monitor")

SEARCHES = [
    "nike tech fleece",
    "nike trainers",
    "arcteryx",
    "zara",
    "raulph lauren quarter zip"
]

CHECK_INTERVAL = 5  # Seconds between checks
SEEN_ITEMS = set()  # Track seen items to avoid duplicates

# -------------------- BOT SETUP --------------------
intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

# -------------------- VINTED SEARCH --------------------
def search_vinted(query):
    url = (
        "https://www.vinted.co.uk/api/v2/catalog/items"
        f"?search_text={query.replace(' ', '%20')}&per_page=5"
    )
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        return r.json().get("items", [])
    except Exception as e:
        print(f"Error fetching {query}: {e}")
        return []

# -------------------- SEND ITEM --------------------
async def send_item(item, channel):
    # Determine role ping
    if ROLE_ID:
        role = channel.guild.get_role(ROLE_ID)
        ping = role.mention if role else "@Monitor"
    else:
        role = discord.utils.get(channel.guild.roles, name=ROLE_NAME)
        ping = role.mention if role else "@Monitor"

    embed = discord.Embed(
        title=item.get("title", "Item"),
        url="https://www.vinted.co.uk" + item.get("url", "/"),
        description=(
            f"{ping}\n\n"
            f"**Price:** £{item.get('price', 'N/A')}\n"
            f"**Brand:** {item.get('brand_title', 'N/A')}\n"
            f"**Size:** {item.get('size_title', 'N/A')}\n"
            f"**Condition:** {item.get('status', 'N/A')}\n"
            f"**Seller:** {item.get('user', {}).get('login', 'N/A')}"
        ),
        color=0x00AEEF
    )

    photo = item.get("photo", {}).get("full_url")
    if photo:
        embed.set_thumbnail(url=photo)

    await channel.send(embed=embed)

# -------------------- MONITOR LOOP --------------------
async def monitor():
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)

    if channel is None:
        print(f"Channel ID {CHANNEL_ID} not found.")
        return

    while not bot.is_closed():
        for query in SEARCHES:
            items = search_vinted(query)
            for item in items:
                item_id = item.get("id")
                if item_id not in SEEN_ITEMS:
                    SEEN_ITEMS.add(item_id)
                    await send_item(item, channel)
        await asyncio.sleep(CHECK_INTERVAL)

# -------------------- BOT EVENTS --------------------
@bot.event
async def on_ready():
    print("Bot online as", bot.user)
    bot.loop.create_task(monitor())  # Start the monitor loop

# -------------------- RUN BOT --------------------
bot.run(TOKEN)
