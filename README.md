# Serverless Telegram Bot for Reddit
This is a demo project of a telegram bot for downloading videos from reddit using AWS and serverless ⚡🤖

Base code taken from [https://github.com/jonatasbaldin/serverless-telegram-bot](https://serverless.com/framework/docs/providers/aws/guide/credentials/).


## Usage

### What do I need?
- A AWS key configured locally, see [here](https://serverless.com/framework/docs/providers/aws/guide/credentials/).
- Python 3.8.
- NodeJS. I tested with v8.9.0.
- A Telegram account.

### Installing
```
# Install the Serverless Framework
$ npm install serverless -g

# Install the necessary plugins
$ npm install

# Create and active a Python 3.8 venv
$ python3.8 -m venv venv && souce venv/bin/activate

# Get a bot from Telegram, sending this message to @BotFather
$ /newbot

# Put the token received into a file called config.json, like this
$ 
TELEGRAM_TOKEN: <your_token>

# Create a SQS queue and a bucket and complete the config.json file

# This will create the queue 
$ aws sqs create-queue --queue-name BotTelegramRedditQueue

# Now use the SQS url to get the ARN and add it to the config.json
$ aws sqs get-queue-attributes --queue-url https://sqs.{region}.amazonaws.com/{account}/BotTelegramRedditQueue --attribute-names All

# Now create a bucket for storing the videos
$ aws s3api create-bucket --bucket reddit-video-upload-bucket --region us-east-1

# Now you need to build the layer with ffmpeg
$ chmod +x build.sh
$ ./build.sh

# Deploy it!
$ serverless deploy

# With the URL returned in the output, configure the Webhook
$ curl -X POST https://<your_url>.amazonaws.com/dev/set_webhook
```

Now, just start a conversation with the bot :)





