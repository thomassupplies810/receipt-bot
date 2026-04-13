import discord
from discord.ext import commands
from discord import app_commands
import os
import time
import asyncio
import datetime

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
    if user_id in user_usage:
        user_usage[user_id] += 1
    else:
        user_usage[user_id] = 1

def get_usage(user_id):
    return user_usage.get(user_id, 0)

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
@bot.tree.command(name="receipt", description="Access premium receipt templates")
@app_commands.describe(type="Select a receipt template")
@app_commands.choices(type=[
    app_commands.Choice(name="Apple", value="apple"),
    app_commands.Choice(name="Cologne", value="cologne"),
    app_commands.Choice(name="Shoes (Coming Soon)", value="shoes"),
])
async def receipt(interaction: discord.Interaction, type: app_commands.Choice[str]):

    user = interaction.user

    # 🔒 Access
    if not has_access(user):
        embed = discord.Embed(
            description="Access restricted to Generator Access members.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # ⏱️ Cooldown
    remaining = check_cooldown(user.id)
    if remaining > 0:
        embed = discord.Embed(
            description=f"You're generating too quickly. Try again in {remaining}s.",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # ⏳ Loading
    await interaction.response.send_message(
        embed=discord.Embed(
            description="⏳ Processing request...\nPreparing your receipt template.",
            color=BRAND_COLOR
        ),
        ephemeral=True
    )

    await asyncio.sleep(1.5)

    # 📂 FILES
    if type.value == "apple":
        file = discord.File("ThomasSupplies_AppleReceipt.docx")
        title = "Apple Receipt"

        embed = discord.Embed(
            title="🧾 Apple Receipt Template",
            description="A professionally structured Apple-style receipt template designed for clean editing and presentation.",
            color=BRAND_COLOR
        )

        embed.add_field(
            name="Template Details",
            value="• Apple-inspired layout\n• Clean formatting\n• Easy customization\n• Microsoft Word compatible",
            inline=False
        )

    elif type.value == "cologne":
        file = discord.File("ThomasSupplies_CologneReceipt.docx")
        title = "Cologne Receipt"

        embed = discord.Embed(
            title="🧾 Fragrance Receipt Template",
            description="A clean and professional fragrance-style receipt template designed for easy customization.",
            color=BRAND_COLOR
        )

        embed.add_field(
            name="Template Details",
            value="• Retail-style layout\n• Clean structure\n• Editable fields\n• Word compatible",
            inline=False
        )

    elif type.value == "shoes":
        embed = discord.Embed(
            title="Coming Soon",
            description="Shoe supplier template is currently in development.",
            color=BRAND_COLOR
        )
        embed.set_footer(text="Thomas Supplies Elite")
        await interaction.edit_original_response(embed=embed)
        return

    # 📊 Usage
    track_usage(user.id)
    usage_count = get_usage(user.id)

    embed.add_field(
        name="How To Use",
        value="1. Open file\n2. Edit details\n3. Save or export",
        inline=False
    )

    embed.set_author(
        name=f"Requested by {user}",
        icon_url=user.display_avatar.url
    )

    embed.set_footer(
        text=f"Thomas Supplies Elite • Uses: {usage_count}"
    )

    await interaction.edit_original_response(
        embed=embed,
        attachments=[file]
    )

    # =========================
    # 📊 LOGGING
    # =========================
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
        description="An error occurred while generating your receipt. Please try again.",
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
