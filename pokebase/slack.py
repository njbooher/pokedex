import os
import requests

from django.core.mail.backends.base import BaseEmailBackend

class SlackEmailBackend(BaseEmailBackend):

    def write_message(self, message):
        msg = message.message()
        msg_data = msg.as_bytes()
        charset = msg.get_charset().get_output_charset() if msg.get_charset() else 'utf-8'
        msg_data = msg_data.decode(charset)
        Notification("Email", msg_data).send()

    def send_messages(self, email_messages):
        if not email_messages:
            return
        msg_count = 0
        try:
            for message in email_messages:
                self.write_message(message)
                msg_count += 1
        except Exception:
            if not self.fail_silently:
                raise

        return msg_count

class Notification(object):

    def __init__(self, title, body):
        self.notification_url = os.getenv('POKEDEX_SLACK_URL', None)
        self.title = title
        self.body = body

    @staticmethod
    def format_markdown_list(items, ordered=False):
        #bullet = "1." if ordered else "*"
        return "\n".join([f"{item}" for item in items])

    def format_body(self):

        body = self.body

        if isinstance(body, list):
            body = Notification.format_markdown_list(body)
        else:
            body = str(self.body)

        if len(body) > 1000:
            body = body[:1000] + "..."

        return body

    def send(self):

        if self.notification_url is None:
            print("notification url was none")
            return

        notification_payload = {
            "text": self.title,
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": self.title
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": self.format_body()
                    }
                },
            ]
        }

        requests.post(self.notification_url, json=notification_payload)