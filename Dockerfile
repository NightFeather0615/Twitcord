FROM python:3.10.6-alpine

WORKDIR /app
COPY . .

ENV DISCORD_BOT_TOKEN your_deploy_token
ENV TWITTER_CONSUMER_KEY your_deploy_key
ENV TWITTER_CONSUMER_SECRET your_deploy_secret
ENV TWITTER_TOKEN your_deploy_token

RUN pip install six resolvelib pdm
RUN pdm install

CMD ["pdm", "run", "python", "main.py"]