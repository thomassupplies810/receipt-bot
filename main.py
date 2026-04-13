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

# =========================
# 🤖 BOT SETUP
# =========================
intents = discord.Intents.default()
intents.message_content = True
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
    current_time = time.time()

    if user_id in user_cooldowns:
        last_used = user_cooldowns[user_id]
        if current_time - last_used < COOLDOWN_TIME:
            return COOLDOWN_TIME - int(current_time - last_used)

    user_cooldowns[user_id] = current_time
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

    for paragraph in doc.paragraphs:
        for key, value in data.items():
            if key in paragraph.text:
                paragraph.text = paragraph.text.replace(key, value)

    doc.save(output_path)

# =========================
# 🚀 BOT READY
# =========================
@bot.event
async def on_ready():
    print(f"Receipt+ is online as {bot.user}")

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

    await bot.change_presence(
        activity=discord.Game("Receipt+ | Thomas Supplies Elite")
    )

# =========================
# 🧾 COMMAND
# =========================
@bot.tree.command(name="receipt", description="Generate a receipt")
@app_commands.describe(
    type="Select a receipt type",
    name="Customer name",
    item="Product name",
    price="Item price",
    cash="Cash paid"
)
@app_commands.choices(type=[
    app_commands.Choice(name="Cologne", value="cologne"),
    app_commands.Choice(name="Apple (Basic)", value="apple"),
])
async def receipt(
    interaction: discord.Interaction,
    type: app_commands.Choice[str],
    name: str,
    item: str,
    price: str,
    cash: str
):

    user = interaction.user

    # 🔒 Access check
    if not has_access(user):
        await interaction.response.send_message(
            embed=discord.Embed(
                description="Access restricted to Generator Access members.",
                color=discord.Color.red()
            ),
            ephemeral=True
        )
        return

    # ⏱️ Cooldown
    remaining = check_cooldown(user.id)
    if remaining > 0:
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"You're generating too quickly. Try again in {remaining}s.",
                color=discord.Color.orange()
            ),
            ephemeral=True
        )
        return

    # ⏳ Loading
    await interaction.response.send_message(
        embed=discord.Embed(
            description="⏳ Generating your receipt...\nPlease wait a moment.",
            color=BRAND_COLOR
        ),
        ephemeral=True
    )

    await asyncio.sleep(1.5)

    # =========================
    # 🧾 COLOGNE AUTOFILL
    # =========================
    if type.value == "cologne":

        price = float(price)
        cash = float(cash)

        tax = round(price * 0.0825, 2)
        total = round(price + tax, 2)
        change = round(cash - total, 2)

        barcode = str(random.randint(10**17, 10**20))

        data = {
            "ITEM_NAME_HERE": item,
            "SUBTOTAL_HERE": f"{price:.2f}",
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
        title = "Cologne Receipt"

    else:
        await interaction.edit_original_response(
            embed=discord.Embed(
                description="This template is not set up for autofill yet.",
                color=discord.Color.red()
            )
        )
        return

    # 📊 Track usage
    track_usage(user.id)
    usage_count = get_usage(user.id)

    # 🧾 Final embed
    embed = discord.Embed(
        title="🧾 Receipt Generated",
        description="Your receipt has been successfully generated.",
        color=BRAND_COLOR
    )

    embed.set_author(name=f"Requested by {user}", icon_url=user.display_avatar.url)
    embed.set_footer(text=f"Thomas Supplies Elite • Uses: {usage_count}")

    await interaction.edit_original_response(
        embed=embed,
        attachments=[file]
    )

    # 📊 Logging
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        log_embed = discord.Embed(
            title="📊 Receipt Generated",
            color=BRAND_COLOR,
            timestamp=datetime.datetime.utcnow()
        )
        log_embed.add_field(name="User", value=f"{user} ({user.id})", inline=False)
        log_embed.add_field(name="Template", value=title, inline=False)
        log_embed.add_field(name="Uses", value=str(usage_count), inline=False)

        await log_channel.send(embed=log_embed)

# =========================
# ❌ ERROR HANDLER
# =========================
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):

    embed = discord.Embed(
        description="An error occurred while generating your receipt.",
        color=discord.Color.red()
    )

    try:
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)
    except:
        pass

    print(error)

# =========================
# 🔑 RUN
# =========================
bot.run(os.getenv("TOKEN"))
