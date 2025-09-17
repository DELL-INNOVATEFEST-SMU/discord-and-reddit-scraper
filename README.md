# discord-and-reddit-scraper
1. To use the sentistrength API:
docker run -p 5000:5000 bulbasaurabh/sentistrength-api
curl -X POST http://localhost:5000/analyze \
     -H "Content-Type: application/json" \
     -d '{"text": "I am feeling amazing today!"}'

2. To use the reddit scraper:
The input subreddits must be in csv format e.g. : SGExams, NationalServiceSG, depression

3. may need environment keys?

4. Because my pc is weird, you need to uncomment the results line and comment the other results line, marked in both files (just search uncomment)
