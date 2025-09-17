import os
import uvicorn
from supabase import create_client, Client
from dotenv import load_dotenv
from sentistrength import PySentiStr
import praw
from google import genai
from google.genai import types
import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict


class ScrapeRequest(BaseModel):
    subreddits: Dict[str, int]

app = FastAPI()
# origins = [
#     "http://localhost:3000",
#     # add other allowed origins if needed, or use ["*"] for all (not recommended in production)
# ]

app.add_middleware(
    CORSMiddleware,
    # allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # allow all HTTP methods
    allow_headers=["*"],  # allow all headers
)


def remove_emojis(text):
    # Emoji unicode ranges based on common patterns
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # Emoticons
        "\U0001F300-\U0001F5FF"  # Symbols & pictographs
        "\U0001F680-\U0001F6FF"  # Transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # Flags
        "\U00002700-\U000027BF"  # Dingbats
        "\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF"  
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)

# Usage:

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
senti.setSentiStrengthPath("./SentiStrength.jar")
senti.setSentiStrengthLanguageFolderPath("./SentiStrengthDataEnglishOctober2019")

# --- User input for multiple subreddits ---
# subreddits = input("Enter subreddits (comma-separated): ").split(",")
# subreddits = [s.strip() for s in subreddits]  # clean whitespace

@app.get("/")
async def root():
    return {"message": "Reddit Scraper is running. Use the /scrape endpoint to start scraping."}

@app.post("/scrape")
async def scrape_subreddits(request: ScrapeRequest):
    await main(request.subreddits)
    return {"status": "Scraping completed"}

async def get_llm_reply(text: str):
    payload = f"Provide a short, uplifting message within 30 words in response to the following:\n\n{text}. Redirect them to this website that allows them to go through a survey to determine their emotions if it was a planet. https://www.mentallyhealthy.sg/assessment"
    response = client.models.generate_content(
    model="gemini-2.5-flash", contents=payload, config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=0) # Disables thinking
    )
)
    
    return response.text

async def main(subreddits):
    for subreddit_name in subreddits.keys():
        subreddit = reddit.subreddit(subreddit_name)
        print(f"📡 Scraping r/{subreddit_name}...")

        # Fetch latest 10 posts
        
        for post in subreddit.new(limit=subreddits[subreddit_name]):
            title = post.title
            body = remove_emojis(post.selftext) or ""
            author = str(post.author) if post.author else "[deleted]"
            url = post.url

            # Combine title + body for sentiment analysis
            text = title + " " + body
            results = senti.getSentiment(text.replace('\n', ''), score='trinary')
            results = results[0] ####uncomment this for trinary sentiment analysis

            # results = senti.getSentiment(text.replace('\n', '')) ####comment this for normal sentiment analysis
            # print(results)
            
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
    uvicorn.run(app, host="0.0.0.0", port=5005)