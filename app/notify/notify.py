import json
from typing import Dict
from urllib.parse import urljoin

import requests
from loguru import logger


class NotifyBot(object):
    def __init__(self, content, title="什么值得买签到", **kwargs: Dict) -> None:
        self.content = content
        self.title = title
        self.kwargs = kwargs

        self.push_plus()
        self.server_chain()
        self.wecom()
        self.tg_bot()
        self.dd_plus()


    def push_plus(self, template="html"):
        if not self.kwargs.get("PUSH_PLUS_TOKEN", None):
            logger.warning("⚠️ PUSH_PLUS_TOKEN not set, skip PushPlus nofitication")
            return
        PUSH_PLUS_TOKEN = self.kwargs.get("PUSH_PLUS_TOKEN")

        url = "https://www.pushplus.plus/send"
        body = {
            "token": PUSH_PLUS_TOKEN,
            "title": self.title,
            "content": self.content,
            "template": template,
        }
        data = json.dumps(body).encode(encoding="utf-8")
        headers = {"Content-Type": "application/json"}
        try:
            resp = requests.post(url, data=data, headers=headers)
            if resp.ok:
                logger.info("✅ Push Plus notified")
            else:
                logger.warning("Fail to notify Push Plus")
        except Exception as e:
            logger.error(e)

    def server_chain(self):
        if not self.kwargs.get("SC_KEY", None):
            logger.warning("⚠️ SC_KEY not set, skip ServerChain notification")
            return
        SC_KEY = self.kwargs.get("SC_KEY")
        url = f"http://sc.ftqq.com/{SC_KEY}.send"
        data = {"text": self.title, "desp": self.content}
        try:
            resp = requests.post(url, data=data)
            if resp.ok:
                logger.info("✅ Server Chain notified")
            else:
                logger.warning("Fail to notify Server Chain")
        except Exception as e:
            logger.error(e)

    def wecom(self):
        if not self.kwargs.get("WECOM_BOT_WEBHOOK", None):
            logger.warning("⚠️ WECOM_BOT_WEBHOOK not set, skip WeCom notification")
            return
        WECOM_BOT_WEBHOOK = self.kwargs.get("WECOM_BOT_WEBHOOK")
        message = {
            "msgtype": "text",
            "text": {"content": f"{self.title}\n{self.content}"},
        }
        try:
            resp = requests.post(WECOM_BOT_WEBHOOK, data=json.dumps(message))
            if resp.ok:
                logger.info("✅ WeCom notified")
            else:
                logger.warning("Fail to notify WeCom")
        except Exception as e:
            logger.error(e)

    def tg_bot(self):
        if not self.kwargs.get("TG_BOT_TOKEN", None) or not self.kwargs.get(
            "TG_USER_ID", None
        ):
            logger.warning("⚠️ Skip TelegramBot notification")
            return
        TG_BOT_TOKEN = self.kwargs.get("TG_BOT_TOKEN")
        TG_USER_ID = self.kwargs.get("TG_USER_ID")
        if self.kwargs.get("TG_BOT_API"):
            url = urljoin(
                self.kwargs.get("TG_BOT_API"), f"/bot{TG_BOT_TOKEN}/sendMessage"
            )
        else:
            url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        params = {
            "chat_id": str(TG_USER_ID),
            "text": f"{self.title}\n{self.content}",
            "disable_web_page_preview": "true",
        }
        try:
            resp = requests.post(url=url, headers=headers, params=params)
            if resp.ok:
                logger.info("✅ Telegram Bot notified")
            else:
                logger.warning("Fail to notify TelegramBot")
        except Exception as e:
            logger.error(e)

    def dd_plus(self, template="html"):
        if not self.kwargs.get("DD_TOKEN", None):
            logger.warning("⚠️ DD_TOKEN not set, skip DingTalk notification")
            return
        DD_TOKEN = self.kwargs.get("DD_TOKEN")
        DD_SECRET = self.kwargs.get("DD_SECRET", None)

        url = f"https://oapi.dingtalk.com/robot/send?access_token={DD_TOKEN}"

        if DD_SECRET:
            import hmac
            import hashlib
            import base64
            import time
            import urllib.parse

            timestamp = str(round(time.time() * 1000))
            secret_enc = DD_SECRET.encode("utf-8")
            string_to_sign = f"{timestamp}\n{DD_SECRET}"
            string_to_sign_enc = string_to_sign.encode("utf-8")
            hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
            sign = urllib.parse.quote_plus(base64.b64encode(hmac_code).decode("utf-8"))
            url = f"{url}&timestamp={timestamp}&sign={sign}"

        # 钉钉 markdown 消息 text 字段最大 20000 字节，超长文本截断
        content_text = self.content
        if len(content_text.encode("utf-8")) > 19000:
            content_text = content_text[:6000] + "\n\n……(内容过长已截断)"

        body = {
            "msgtype": "markdown",
            "markdown": {
                "title": self.title[:200],  # 钉钉限制标题 200 字符
                "text": content_text,
            },
        }
        data = json.dumps(body).encode(encoding="utf-8")
        headers = {"Content-Type": "application/json"}
        try:
            resp = requests.post(url, data=data, headers=headers)
            if resp.ok:
                logger.info("✅ DingTalk notified")
            else:
                logger.warning(f"Fail to notify DingTalk: status={resp.status_code} body={resp.text[:200]}")
        except Exception as e:
            logger.error(f"DingTalk request failed: {e}")

