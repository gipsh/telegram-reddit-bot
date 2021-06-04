import json
import telegram
import youtube_dl
from urllib.parse import urlparse
import boto3
from botocore.exceptions import ClientError
import os
import logging


# Logging is cool!
logger = logging.getLogger()
if logger.handlers:
    for handler in logger.handlers:
        logger.removeHandler(handler)
logging.basicConfig(level=logging.INFO)

OK_RESPONSE = {
    'statusCode': 200,
    'headers': {'Content-Type': 'application/json'},
    'body': json.dumps('ok')
}
ERROR_RESPONSE = {
    'statusCode': 400,
    'body': json.dumps('Oops, something went wrong!')
}


def configure_telegram():
    """
    Configures the bot with a Telegram Token.
    Returns a bot instance.
    """

    TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
    if not TELEGRAM_TOKEN:
        logger.error('The TELEGRAM_TOKEN must be set')
        raise NotImplementedError

    return telegram.Bot(TELEGRAM_TOKEN)


def webhook(event, context):
    """
    Runs the Telegram webhook.
    """

    bot = configure_telegram()
    logger.info('Event: {}'.format(event))

    if event.get('httpMethod') == 'POST' and event.get('body'): 
        logger.info('Message received')
        update = telegram.Update.de_json(json.loads(event.get('body')), bot)
        chat_id = update.message.chat.id
        text = update.message.text

        logger.info(update.message)
        if text == '/start':
            text = """Hello, human! I am an carlo killer bot, send me a reddit post i will sent you the video back.
            You can take a look at my source code here: https://github.com/gipsh/telegram-reddit-bot.
            Enjoy!"""

            bot.sendMessage(chat_id=chat_id, text=text)

            return OK_RESPONSE


        if is_reddit(text):
            # send to queue
            sqs = boto3.client("sqs", region_name=os.getenv('AWS_REGION'))

            response = sqs.get_queue_url(
                         QueueName=os.getenv('SQS_QUEUE_NAME'),
                    )
            
            queue_url = response["QueueUrl"]

            messageBody = {
                    "url": text,
                    "chat_id": update.message.chat.id,
                    "first_name": update.message.chat.first_name,
                    "last_name": update.message.chat.last_name
            }

            
            response = sqs.send_message(
                QueueUrl=queue_url,
                DelaySeconds=10,
                MessageAttributes={
                 'Metadata': {
                    'DataType': 'String',
                    'StringValue': 'The Whistler'
                 }
                },
                MessageBody=(
                    json.dumps(messageBody)
                )
            )

            logger.info(response['MessageId'])
            bot.sendMessage(chat_id=chat_id, text=response['MessageId'])
        else:
            bot.sendMessage(chat_id=chat_id, text='not a reddit post')
        
        logger.info('Message sent')

        return OK_RESPONSE

    return ERROR_RESPONSE


def set_webhook(event, context):
    """
    Sets the Telegram bot webhook.
    """

    logger.info('Event: {}'.format(event))
    bot = configure_telegram()
    url = 'https://{}/{}/'.format(
        event.get('headers').get('Host'),
        event.get('requestContext').get('stage'),
    )
    webhook = bot.set_webhook(url)

    if webhook:
        return OK_RESPONSE

    return ERROR_RESPONSE


def download_worker(event, context):
    """
    Download a video store on s3
    """

    logger.info('Event: {}'.format(event))

    for record in event['Records']:
        payload = record["body"]
        logger.info("payload is: {}".format(payload))
        d = json.loads(str(payload))
        print(d['chat_id'])
        print(d['url'])
        
        ydl = youtube_dl.YoutubeDL(
            {'format': 'worstvideo[container=mp4_dash]+worstaudio',
            'ffmpeg_location': '/opt/ffmpeg/ffmpeg',
            'outtmpl': '/tmp/%(id)s.%(ext)s'})

        with ydl:
            result = ydl.extract_info(
                d['url'],
                download=True 
            )

        logger.info(result) 
        
        output = '/tmp/{}.{}'.format(result['id'], result['ext'])

        dest = 'reddit/{}.{}'.format(result['id'], result['ext'])

        s3 = boto3.client('s3')

        # upload the file
        try:
            response = s3.upload_file(output, os.getenv('S3_BUCKET'), dest,
                    ExtraArgs={'Metadata': {'url': d['url'],
                                            'name': "{} {}".format(d['first_name'], d['last_name']),
                                            'title': result['title'] }} )
        except ClientError as e:
            logger.error(e)

        # once upladed get the pre signed url
        response = s3.generate_presigned_url('get_object',
                        Params={'Bucket': os.getenv('S3_BUCKET'),
                                'Key': dest},
                                 ExpiresIn=3600)

        bot = configure_telegram()
        bot.sendMessage(chat_id=d['chat_id'], text="{}".format(response))

        
   


def is_reddit(ii):
    o = urlparse(ii)
    return (o.netloc == 'www.reddit.com')
