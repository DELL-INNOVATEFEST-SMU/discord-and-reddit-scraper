import os
import discord
from discord.ext import commands
from google.genai import types
from dotenv import load_dotenv
from supabase import create_client, Client
from sentistrength import PySentiStr
from google import genai


senti = PySentiStr()
senti.setSentiStrengthPath("./SentiStrength.jar")
senti.setSentiStrengthLanguageFolderPath("./SentiStrengthDataEnglishOctober2019")
load_dotenv()  # take environment variables from .env.

# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True  # needed to read messages
intents.members = True          # needed for DM access

bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize sentiment analyzer
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=GOOGLE_API_KEY)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Events ---

@bot.event
async def on_ready():
    print(f"✅ Bot logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} commands")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")

async def get_llm_reply(text: str):
    payload = f"Provide a short, uplifting message within 30 words in response to the following:\n\n{text}. Redirect them to this website that allows them to go through a survey to determine their emotions if it was a planet. https://www.mentallyhealthy.sg/assessment"
    response = client.models.generate_content(
        model="gemini-2.5-flash", contents=payload, config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=0) # Disables thinking
        )
    )
    return response.text


@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return

    # Run sentiment analysis
    
    # Save ALL messages to Supabase
    results = senti.getSentiment(message.content)

    print(results)  

    # If message is strongly negative, DM user
    if results[1] < -2 :
        try:
            llm_reply = await get_llm_reply(message.content)
            supabase.table("messages").insert({
                "username": str(message.author),
                "content": message.content,
                "score": results[1],
                "source": "discord",
                "link": message.guild.name if message.guild else "DM",
                "suggested_outreach": llm_reply
            }).execute()
            

            await message.author.send(
                f"💙 Hey {message.author.name}, I noticed your message seemed really tough. "
                f"If you’re in Singapore, you can reach out to **SAMH** (https://www.samhealth.org.sg/) "
                f"or call **SOS 1767** (24/7 support). You are not alone. 💙"
                f"\n\nAlso, here's a little something from me: {llm_reply}"
            )
            print(f"DM sent to {message.author}")
        except discord.Forbidden:
            print(f"❌ Cannot DM {message.author} (privacy settings).")

    await bot.process_commands(message)
# --- Slash Commands ---

@bot.tree.command(name="dailycheckin", description="Check in with yourself today")
async def dailycheckin(interaction: discord.Interaction):
    await interaction.response.send_message(
        "🌱 Daily Check-In 🌱\n\n"
        "How are you feeling today? Try to pause and notice:\n"
        "• One positive thing that happened\n"
        "• One challenge you faced\n"
        "• One small step you can take tomorrow 💪",
        ephemeral=True
    )

@bot.tree.command(name="resources", description="Get mental health resources")
async def resources(interaction: discord.Interaction):
    await interaction.response.send_message(
        "📖 Here are some mental health resources in Singapore:\n"
        "- SAMH: https://www.samh.org.sg/\n"
        "- SOS Hotline (24/7): 1767\n"
        "- mindline.sg: https://mindline.sg/\n"
        "- IMH Helpline: 6389 2222",
        ephemeral=True
    )

TOKEN = os.getenv("DISCORD_TOKEN")  # set your token in environment variable
bot.run(TOKEN)