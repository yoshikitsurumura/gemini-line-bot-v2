
from flask import Flask, request, abort

from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

import os
import sys
import google.generativeai as genai

app = Flask(__name__)

# 環境変数からLINEのチャネルシークレットとチャネルアクセストークンを取得
channel_secret = "ea5ca94e41c9f749ff4289a4910ca909"
channel_access_token = "zgQUqALs1EVvGHFQItEUTfCw8cEeLuYnpn1LyVAJFn07CNmP4yX4BpIWKCwhlY3JSBLblEtnQc09329Nkv6nU4lkqsJ6eSKEAPTLrYFDTG5wh6FvLHB0BAPA2AlsV+kweO2Nbd6lZ4T4zqDcWd3mwQdB04t89/1O/w1cDnyilFU="

# 環境変数からGemini APIキーを取得
gemini_api_key = "AIzaSyDsrbJzdQ6S2pj9mPr_hSWcCK_UdpJB-fg"

if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)
if gemini_api_key is None:
    print('Specify GEMINI_API_KEY as environment variable.')
    sys.exit(1)

# Gemini APIの設定
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-pro')

handler = WebhookHandler(channel_secret)

configuration = Configuration(
    access_token=channel_access_token
)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_message = event.message.text
    reply_text = ""

    try:
        # Geminiにメッセージを送信し、応答を取得
        response = model.generate_content(user_message)
        reply_text = response.text
    except Exception as e:
        # エラーが発生した場合は、エラーメッセージを返信
        reply_text = f"AIの応答中にエラーが発生しました: {e}"
        app.logger.error(f"Gemini API Error: {e}")

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
