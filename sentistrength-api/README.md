# sentiStrength
1. To use the sentistrength API:

```bash

docker build -t sentistrength-api:latest .
docker run -p 5000:5000 sentistrength-api:latest


curl -X POST http://localhost:5000/analyze \
     -H "Content-Type: application/json" \
     -d '{"text": "I am feeling amazing today!"}'
```

2. pushing to harbour

```bash


```
