import discord
from discord.ext import commands
from discord import app_commands
import os
import time
import asyncio
import datetime
import random
from docx import Document

# =========================
# ⚙️ CONFIG
# =========================
ROLE_NAME = "📄 Generator Access"
LOG_CHANNEL_ID = 1493091757364088965
COOLDOWN_TIME = 5
BRAND_COLOR = 0x1A3DFF
TAX_RATE = 0.0825

# =========================
# 🤖 BOT SETUP
# =========================
intents = discord.Intents.default()
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# 🧠 STORAGE
# =========================
user_cooldowns = {}
user_usage = {}

# =========================
# 🔐 ROLE CHECK
# =========================
def has_access(user):
    return any(role.name == ROLE_NAME for role in user.roles)

# =========================
# ⏱️ COOLDOWN
# =========================
def check_cooldown(user_id):
    now = time.time()
    if user_id in user_cooldowns:
        if now - user_cooldowns[user_id] < COOLDOWN_TIME:
            return COOLDOWN_TIME - int(now - user_cooldowns[user_id])
    user_cooldowns[user_id] = now
    return 0

# =========================
# 📊 USAGE TRACKING
# =========================
def track_usage(user_id):
    user_usage[user_id] = user_usage.get(user_id, 0) + 1

def get_usage(user_id):
    return user_usage.get(user_id, 0)

# =========================
# 🧾 DOCX GENERATOR
# =========================
def generate_receipt(template_path, output_path, data):
    doc = Document(template_path)

    for p in doc.paragraphs:
        for key, value in data.items():
            if key in p.text:
                p.text = p.text.replace(key, value)

    doc.save(output_path)

# =========================
# 🚀 READY
# =========================
@bot.event
async def on_ready():
    print(f"Receipt+ running as {bot.user}")
    await bot.tree.sync()

# =========================
# 🧾 COMMAND
# =========================
@bot.tree.command(name="receipt", description="Generate a professional receipt")
@app_commands.describe(
    type="Select receipt type",
    product_name="Product purchased",
    price="Item price (numbers only)",
    amount_paid="Cash provided"
)
@app_commands.choices(type=[
    app_commands.Choice(name="Cologne Receipt", value="cologne"),
])
async def receipt(
    interaction: discord.Interaction,
    type: app_commands.Choice[str],
    product_name: str,
    price: str,
    amount_paid: str
):

    user = interaction.user

    # 🔒 Role check
    if not has_access(user):
        return await interaction.response.send_message(
            "Access restricted.",
            ephemeral=True
        )

    # ⏱️ Cooldown
    remaining = check_cooldown(user.id)
    if remaining > 0:
        return await interaction.response.send_message(
            f"Wait {remaining}s before generating again.",
            ephemeral=True
        )

    await interaction.response.send_message(
        "⏳ Generating receipt...",
        ephemeral=True
    )

    await asyncio.sleep(1.2)

    # =========================
    # 🧾 COLOGNE AUTOFILL
    # =========================
    if type.value == "cologne":

        price = float(price)
        cash = float(amount_paid)

        subtotal = price
        tax = round(subtotal * TAX_RATE, 2)
        total = round(subtotal + tax, 2)
        change = round(cash - total, 2)

        barcode = str(random.randint(10**17, 10**20))

        data = {
            "ITEM_NAME_HERE": product_name,
            "SUBTOTAL_HERE": f"{subtotal:.2f}",
            "TAX_HERE": f"{tax:.2f}",
            "TOTAL_HERE": f"{total:.2f}",
            "CASH_HERE": f"{cash:.2f}",
            "CHANGE_HERE": f"{change:.2f}",
            "DATE_HERE": datetime.datetime.now().strftime("%m/%d/%Y"),
            "TIME_HERE": datetime.datetime.now().strftime("%I:%M %p"),
            "BARCODE_NUMBER_HERE": barcode
        }

        output_file = f"receipt_{user.id}.docx"

        generate_receipt(
            "ThomasSupplies_CologneReceipt.docx",
            output_file,
            data
        )

        file = discord.File(output_file)

    # =========================
    # 📊 TRACK + SEND
    # =========================
    track_usage(user.id)

    await interaction.edit_original_response(
        content="✅ Receipt generated successfully.",
        attachments=[file]
    )

# =========================
# ❌ ERROR HANDLER
# =========================
@bot.tree.error
async def on_app_command_error(interaction, error):
    print(error)

# =========================
# 🔑 RUN
# =========================
bot.run(os.getenv("TOKEN"))
