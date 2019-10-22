# coding=utf-8
import logging
import logging.handlers
import platform
import subprocess
import threading
import time
import tkinter.font as tkfont
import urllib.request
from tkinter import *
from urllib.parse import quote

from bs4 import BeautifulSoup
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Module(Base):
    # 表名称
    __tablename__ = 'zhidao'
    id = Column(Integer, primary_key=True, autoincrement=True)
    answer = Column(String(length=255), nullable=False)
    content = Column(Text, nullable=True)

    def to_dict(self):
        return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}


class Question:
    def __init__(self):
        # 创建Logger
        self.logger = logging.getLogger('zhidao')
        self.logger.setLevel(logging.DEBUG)
        # 创建Handler

        # 终端Handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        # 文件Handler
        file_handler = logging.handlers.TimedRotatingFileHandler("./zhidao.log", when='D', interval=3,
                                                                 backupCount=40)
        file_handler.suffix = "%Y-%m-%d.log"
        file_handler.setLevel(logging.NOTSET)

        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        # 添加到Logger中
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    @staticmethod
    def get_answer_form_network(content):
        url = 'http://xuexi.xuanxiu365.com/index.php?time=%s&q=%s' % (int(time.time()), quote(content))
        r = urllib.request.urlopen(url, timeout=10)
        module = Module()
        if r is not None:
            html = BeautifulSoup(r.read().decode('utf-8').replace('', ' '), 'lxml')
            answer_tag = html.find(text='正确答案是：')
            if answer_tag is not None:
                question_tag = html.find(text='题目：')
                module.answer = answer_tag.parent.next_sibling.string
                module.content = question_tag.parent.next_sibling.string
                with open('answer.txt', 'a', encoding='utf8') as f:
                    f.write(str(module.to_dict()))
                    f.write('\n')
                return module
        return None

    def init_gui(self):

        root = Tk()

        # noinspection PyUnusedLocal
        # 获取答案
        def callback(event):
            try:
                string = root.clipboard_get()
                if string is not None and string != '':
                    try:
                        m = self.get_answer_form_network(string)
                        if m is None:
                            content.set(string)
                            text.set('没有答案')
                        else:
                            content.set(m.content)
                            text.set(m.answer)
                    except Exception as e:
                        text.set('出现异常')
                        self.logger.error(e)
                else:
                    content.set('')
            except TclError:
                pass

        self_platform = platform.system()
        if self_platform == "Darwin":
            # 不可用
            # subprocess.call(
            #     ["/usr/bin/osascript", "-e", 'tell app "Finder" to set frontmost of process "Python" to true'])
            # root.bind('<Command-c>', callback)
            # root.bind('<Command-C>', callback)
            def watch_clip(top):
                import time
                last_str = None
                while True:
                    time.sleep(0.01)
                    now_str = root.clipboard_get()
                    if last_str is None or (last_str != now_str):
                        if last_str is not None:
                            top.event_generate("<<clipUpdateEvent>>", when="tail")
                        last_str = now_str
        else:
            def watch_clip(top):
                import win32clipboard
                import time
                lastid = None
                while True:
                    time.sleep(0.01)
                    nowid = win32clipboard.GetClipboardSequenceNumber()
                    if lastid is None or (lastid != nowid):
                        if lastid is not None:
                            top.event_generate("<<clipUpdateEvent>>", when="tail")
                        lastid = nowid

        t = threading.Thread(target=watch_clip, args=(root,), daemon=True)
        t.start()

        ft = tkfont.Font(family='Fixdsys', size=16, weight=tkfont.BOLD)

        content = StringVar()
        text = StringVar()

        label1 = Label(root, justify=LEFT, bg='red', textvariable=content)
        label1.pack(fill=X)

        # from tkinter import Text as TKText
        # T = TKText(root, font=ft)
        # T.pack()

        root.bind('<Button-2>', callback)

        root.bind("<<clipUpdateEvent>>", callback)

        label2 = Label(root, justify=CENTER, wraplength=300, textvariable=text, fg='red', font=ft)
        label2.pack()

        def center_window(w, h):
            # 获取屏幕 宽、高
            ws = root.winfo_screenwidth()
            hs = root.winfo_screenheight()
            # 计算 x, y 位置
            x = (ws / 2) - (w / 2)
            y = (hs / 2) - (h / 2)
            root.geometry('%dx%d+%d+%d' % (w, h, x, y))

        center_window(300, 250)
        root.mainloop()


if __name__ == '__main__':
    q = Question()
    q.init_gui()
