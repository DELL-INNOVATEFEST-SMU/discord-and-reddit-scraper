import os
from supabase import create_client, Client
from dotenv import load_dotenv
from sentistrength import PySentiStr
import praw
from google import genai
from google.genai import types
#hi kevin
# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=GOOGLE_API_KEY)

# Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Reddit client
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT,
)

# Initialize SentiStrength
senti = PySentiStr()
senti.setSentiStrengthPath("C:/wamp64/www/SentiStrength.jar")
senti.setSentiStrengthLanguageFolderPath("C:/wamp64/www/SentiStrengthDataEnglishOctober2019")

# --- User input for multiple subreddits ---
subreddits = input("Enter subreddits (comma-separated): ").split(",")
subreddits = [s.strip() for s in subreddits]  # clean whitespace

async def get_llm_reply(text: str):
    payload = f"Provide a short, uplifting message within 30 words in response to the following:\n\n{text}. Redirect them to this website that allows them to go through a survey to determine their emotions if it was a planet. https://www.mentallyhealthy.sg/assessment"
    response = client.models.generate_content(
    model="gemini-2.5-flash", contents=payload, config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=0) # Disables thinking
    )
)
    
    return response.text

async def main(subreddits):
    for subreddit_name in subreddits:
        subreddit = reddit.subreddit(subreddit_name)
        print(f"📡 Scraping r/{subreddit_name}...")

        # Fetch latest 10 posts
        for post in subreddit.new(limit=10):
            title = post.title
            body = post.selftext or ""
            author = str(post.author) if post.author else "[deleted]"
            url = post.url

            # Combine title + body for sentiment analysis
            text = title + " " + body
            results = senti.getSentiment(text.replace('\n', ''))

            # If negative sentiment is strong, save to Supabase
            if results[1] < -2:  # adjustable threshold
                try:
                    llm_reply = await get_llm_reply(body.split('\n')[0] if body else title)
                    supabase.table("messages").insert({
                        "username": author,
                        "content": body,
                        "score": results[1],
                        "source": "reddit",
                        "link": url,
                        "suggested_outreach": llm_reply
                    }).execute()
                    print(f"✅ Saved negative post from r/{subreddit_name}: {title}")
                except Exception as e:
                    print(f"❌ Could not save post {title}: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main(subreddits))
