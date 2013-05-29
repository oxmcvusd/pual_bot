#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
#   Author  :   cold
#   E-mail  :   wh_linux@126.com
#   Date    :   13/03/01 11:44:05
#   Desc    :   消息调度
#
import re
import logging
from functools import partial

from command import Command
from config import MAX_RECEIVER_LENGTH


code_typs = ['actionscript', 'ada', 'apache', 'bash', 'c', 'c#', 'cpp',
              'css', 'django', 'erlang', 'go', 'html', 'java', 'javascript',
              'jsp', 'lighttpd', 'lua', 'matlab', 'mysql', 'nginx',
              'objectivec', 'perl', 'php', 'python', 'python3', 'ruby',
              'scheme', 'smalltalk', 'smarty', 'sql', 'sqlite3', 'squid',
              'tcl', 'text', 'vb.net', 'vim', 'xml', 'yaml']

ABOUT_STR = u"Author    :   cold\nE-mail    :   wh_linux@126.com\n"\
        u"HomePage  :   http://t.cn/zTocACq\n"\
        u"Project@  :   http://git.io/hWy9nQ"

HELP_DOC =  u"http://paste.linuxzen.com/p/Mzcw/text"
u"""Pual 使用指南:
    -tr <content>    可以对<content>进行英汉互译
    ```<type>\\n<code>  可以将<code>以<type>高亮的方式贴到http://paste.linuxzen.com
    >>> <statement>  可以执行Python语句, 并为你个人将这个语句产生的定义放在服务器
    ping Pual        可以查看Pual是否在线
    about Pual       可以查看Pual相关信息
    help Pual        显示本信息
"""


URL_RE = re.compile(r"(http[s]?://(?:[-a-zA-Z0-9_]+\.)+[a-zA-Z]+(?::\d+)"
                    "?(?:/[-a-zA-Z0-9_%./]+)*\??[-a-zA-Z0-9_&%=.]*)",
                    re.UNICODE)

class MessageDispatch(object):
    """ 消息调度器 """
    def __init__(self, webqq):
        self.webqq = webqq
        self.cmd = Command()

    def send_msg(self, content, callback, nick = None):
        self.cmd.send_msg(content, callback, nick)

    def handle_qq_msg_contents(self, contents):
        content = ""
        for row in contents:
            if isinstance(row, (str, unicode)):
                content += row.replace(u"【提示：此用户正在使用Q+"
                                       u" Web：http://web.qq.com/】", "")\
                        .replace(u"【提示：此用户正在使用Q+"
                                       u" Web：http://web3.qq.com/】", "")
        return  content.replace("\r", "\n").replace("\r\n", "\n")\
                .replace("\n\n", "\n")


    def handle_qq_group_msg(self, message):
        """ 处理组消息 """
        value = message.get("value", {})
        gcode = value.get("group_code")
        uin = value.get("send_uin")
        contents = value.get("content", [])
        content = self.handle_qq_msg_contents(contents)
        uname = self.webqq.get_group_member_nick(gcode, uin)
        if content:
            pre = u"{0}: ".format(uname)
            callback = partial(self.webqq.send_group_msg, gcode)
            self.handle_content(uin, content, callback, pre)


    def handle_qq_message(self, message):
        """ 处理QQ好友消息 """
        value = message.get("value", {})
        from_uin = value.get("from_uin")
        contents = value.get("content", [])
        content = self.handle_qq_msg_contents(contents)
        if content:
            callback = partial(self.webqq.send_buddy_msg, from_uin)
            self.handle_content(from_uin, content, callback)

    def handle_content(self, from_uin, content, callback, pre = None):
        """ 处理内容
        Arguments:
            `from_uin`  -       发送者uin
            `content`   -       内容
            `callback`  -       仅仅接受内容参数的回调
            `pre`       -       处理后内容前缀
        """
        send_msg = partial(self.send_msg, callback = callback, nick = pre)

        urls = URL_RE.findall(content)
        if urls:
            logging.info(u"Get urls {0!r} from {1}".format(urls, content))
            for url in urls:
                self.cmd.url_info(url, send_msg)

        if content.startswith("-py"):
            body = content.lstrip("-py").strip()
            self.cmd.py(body, send_msg)
            return

        if content.startswith("```"):
            typ = content.split("\n")[0].lstrip("`").strip().lower()
            if typ not in code_typs: typ = "text"
            code = "\n".join(content.split("\n")[1:])
            self.cmd.paste(code, send_msg, typ)
            return

        if content.strip().lower() == "ping " + self.webqq.nickname.lower():
            body = u"I am here ^ ^"
            send_msg(body)
            return

        if content.strip().lower() == "about " + self.webqq.nickname.lower():
            body = ABOUT_STR
            send_msg(body)
            return

        if content.strip().lower() == "help " + self.webqq.nickname.lower():
            send_msg(HELP_DOC)
            return

        if content.strip() == "uptime " + self.webqq.nickname:
            body = self.webqq.get_uptime()
            send_msg(body)
            return

        if content.startswith("Pual"):
            content = content.strip("Pual ")
            if content:
                self.cmd.simsimi(content, send_msg)
            else:
                send_msg(u"你总的说点什么吧")
            return

        if content.startswith("-tr"):
            if content.startswith("-trw"):
                web = True
                st = "-trw"
            else:
                web = False
                st = "-tr"
            body = content.lstrip(st).strip()
            self.cmd.cetr(body, send_msg, web)
            return

        if content.startswith(">>>"):
            body = content.lstrip(">").lstrip(" ")
            self.cmd.shell(from_uin, body, send_msg)


        if u"提问的智慧" in content:
            bodys = []
            bodys.append(u"提问的智慧:")
            bodys.append(u"原文: http://t.cn/hthAh")
            bodys.append(u"译文: http://t.cn/SUHbCJ")
            bodys.append(u"简化版: http://t.cn/hI2oe")
            bodys.append(u"概括:")
            bodys.append(u"1. 详细描述问题: 目的, 代码, 错误信息等")
            bodys.append(u"2. 代码不要直接发到QQ上, 以免被替换成表情或丢失缩进")
            bodys.append(u"3. 向帮你解决问题的人说谢谢 ")
            callback("\n".join(bodys))



        if len(content) > MAX_RECEIVER_LENGTH:
            if pre:
                cpre = u"{0}内容过长: ".format(pre)
            else:
                cpre = pre
            send_pre_msg = partial(self.send_msg, callback = callback, nick = cpre)
            self.cmd.paste(content, send_pre_msg)


    def dispatch(self, qq_source):
        if qq_source.get("retcode") == 0:
            messages = qq_source.get("result")
            for m in messages:
                if m.get("poll_type") == "group_message":
                    self.handle_qq_group_msg(m)
                if m.get("poll_type") == "message":
                    self.handle_qq_message(m)
                if m.get("poll_type") == "kick_message":
                    self.webqq.stop()
