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
# CONFIG
# =========================
ROLE_NAME = "📄 Generator Access"
LOG_CHANNEL_ID = 1493091757364088965
COOLDOWN_TIME = 5

COLOGNE_TAX = 0.0825
APPLE_TAX = 0.0904

# =========================
# BOT SETUP
# =========================
intents = discord.Intents.default()
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

user_cooldowns = {}

# =========================
# ROLE CHECK
# =========================
def has_access(user):
    return any(role.name == ROLE_NAME for role in user.roles)

# =========================
# COOLDOWN
# =========================
def check_cooldown(user_id):
    now = time.time()
    if user_id in user_cooldowns:
        if now - user_cooldowns[user_id] < COOLDOWN_TIME:
            return COOLDOWN_TIME - int(now - user_cooldowns[user_id])
    user_cooldowns[user_id] = now
    return 0

# =========================
# 🔥 FIXED DOCX ENGINE
# =========================
def generate_receipt(template_path, output_path, data, make_bold=False):
    doc = Document(template_path)

    for paragraph in doc.paragraphs:
        full_text = paragraph.text

        for key, value in data.items():
            if key in full_text:
                full_text = full_text.replace(key, value)

        if paragraph.text != full_text:
            paragraph.clear()
            run = paragraph.add_run(full_text)

            if make_bold:
                run.bold = True

    doc.save(output_path)

# =========================
# READY
# =========================
@bot.event
async def on_ready():
    print(f"Bot running as {bot.user}")
    await bot.tree.sync()

# =========================
# COMMAND
# =========================
@bot.tree.command(name="receipt", description="Generate a receipt")
@app_commands.describe(
    type="Receipt type",
    product_name="Product name",
    price="Item price",
    amount_paid="Cash (for cologne only)"
)
@app_commands.choices(type=[
    app_commands.Choice(name="Cologne Receipt", value="cologne"),
    app_commands.Choice(name="AirPods Receipt", value="airpods"),
])
async def receipt(
    interaction: discord.Interaction,
    type: app_commands.Choice[str],
    product_name: str,
    price: str,
    amount_paid: str
):

    user = interaction.user

    # Role check
    if not has_access(user):
        return await interaction.response.send_message(
            "Access restricted.",
            ephemeral=True
        )

    # Cooldown
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

    price = float(price)

    # =========================
    # COLOGNE
    # =========================
    if type.value == "cologne":

        cash = float(amount_paid)

        subtotal = price
        tax = round(subtotal * COLOGNE_TAX, 2)
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

        file_name = f"Cologne_Receipt_{random.randint(1000,9999)}.docx"

        generate_receipt(
            "ThomasSupplies_CologneReceipt.docx",
            file_name,
            data,
            make_bold=True
        )

    # =========================
    # AIRPODS
    # =========================
    elif type.value == "airpods":

        subtotal = price
        tax = round(subtotal * APPLE_TAX, 2)
        total = round(subtotal + tax, 2)

        barcode = str(random.randint(10**17, 10**20))
        card_last4 = random.randint(1000, 9999)

        data = {
            "PRODUCT_NAME_HERE": product_name,
            "PRICE_HERE": f"{price:.2f}",
            "SUBTOTAL_HERE": f"{subtotal:.2f}",
            "TAX_HERE": f"{tax:.2f}",
            "TOTAL_HERE": f"{total:.2f}",
            "BARCODE_HERE": barcode,
            "CARD_LAST4_HERE": str(card_last4),
            "DATE_FULL_HERE": datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        }

        file_name = f"AirPods_Receipt_{random.randint(1000,9999)}.docx"

        generate_receipt(
            "ThomasSupplies_AppleReceipt.docx",
            file_name,
            data,
            make_bold=False
        )

    file = discord.File(file_name)

    await interaction.edit_original_response(
        content="✅ Receipt ready.",
        attachments=[file]
    )

# =========================
# ERROR HANDLER
# =========================
@bot.tree.error
async def on_app_command_error(interaction, error):
    print(error)

# =========================
# RUN
# =========================
bot.run(os.getenv("TOKEN"))
