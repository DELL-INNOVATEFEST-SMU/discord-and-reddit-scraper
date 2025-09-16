Commands:

```bash
docker login ihl-harbor.apps.innovate.sg-cna.com
docker build -t discord-bot:latest .
docker tag discord-bot:latest ihl-harbor.apps.innovate.sg-cna.com/smu/discord-bot:latest
docker push ihl-harbor.apps.innovate.sg-cna.com/smu/discord-bot:latest
```