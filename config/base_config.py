# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/futianren/KidsTaiChi-MediaCrawler/blob/main/config/base_config.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#

# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：
# 1. 不得用于任何商业用途。
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。
# 3. 不得进行大规模爬取或对平台造成运营干扰。
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。
# 5. 不得用于任何非法或不当的用途。
#
# 详细许可条款请参阅项目根目录下的LICENSE文件。
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。

# Basic configuration
PLATFORM = "xhs"  # Platform, xhs | dy | ks | bili | wb | tieba | zhihu

# 是否使用海外版小红书 (rednote.com)
# 开启后 API 走 webapi.rednote.com，cookie 域使用 .rednote.com
XHS_INTERNATIONAL = False

KEYWORDS = "编程副业,编程兼职"  # Keyword search configuration, separated by English commas
LOGIN_TYPE = "qrcode"  # qrcode or phone or cookie
COOKIES = ""
CRAWLER_TYPE = "search"
# Whether to enable IP proxy
ENABLE_IP_PROXY = False

# Number of proxy IP pools
IP_PROXY_POOL_COUNT = 2

# Proxy IP provider name
IP_PROXY_PROVIDER_NAME = "kuaidaili"  # kuaidaili | wandouhttp

# Setting to True will not open the browser (headless browser)
# Setting False will open a browser
# If Xiaohongshu keeps scanning the code to log in but fails, open the browser and manually pass the sliding verification code.
# If Douyin keeps prompting failure, open the browser and see if mobile phone number verification appears after scanning the QR code to log in. If it does, manually go through it and try again.
# 项目默认无头：批量/服务器环境不弹窗；需过滑块/验证码时可改为 False 或命令行 --headless false
HEADLESS = True

# Whether to save login status
SAVE_LOGIN_STATE = True

# ==================== Playwright storage_state（非 CDP 默认）====================
# 会话文件根目录（相对项目工作目录）；每平台子目录下放 COOKIES_STORAGE_FILENAME
COOKIES_STORAGE_ROOT = "cookiesFile"
COOKIES_STORAGE_FILENAME = "session.json"
# 可选：使用本机 Google Chrome 通道（需已安装 Chrome）。空字符串表示由代码按平台决定（xhs/dy 等默认 channel=chrome）。
PLAYWRIGHT_CHANNEL = ""
# 可选：浏览器可执行文件路径（例如 C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe）。
# 与参考项目 conf.py 的 LOCAL_CHROME_PATH 同义：指向本机 chrome.exe；非空时优先于 PLAYWRIGHT_CHANNEL。
# 一般不必填写：默认 channel=chrome 已会启动本机已安装的 Google Chrome。
PLAYWRIGHT_EXECUTABLE_PATH = ""
# 为 True 时，启动的 Chromium/Chrome 不使用系统/环境变量中的代理（WinINet、PAC、HTTP_PROXY 等）。
# 开启 ENABLE_IP_PROXY 时仍通过 Playwright 的 context proxy 走 IP 池；若与第三方代理工具冲突可改为 False。
PLAYWRIGHT_IGNORE_SYSTEM_PROXY = True

# ==================== CDP (Chrome DevTools Protocol) 配置 ====================
# 是否启用 CDP 模式 - 使用用户本地的 Chrome/Edge 浏览器进行爬取，具有更好的反检测能力
# 开启后，会自动检测并启动用户的 Chrome/Edge 浏览器，通过 CDP 协议进行控制
# 该方式使用真实浏览器环境，包括用户的扩展、Cookie 和设置，大幅降低被风控检测的风险
# 默认 False：使用自启 Chromium/Chrome + cookiesFile/<platform>/session.json 持久化
ENABLE_CDP_MODE = False

# CDP 调试端口，用于与浏览器通信
# 如果端口被占用，系统会自动尝试下一个可用端口
CDP_DEBUG_PORT = 9222

# 无头/自动化抓取时，若本机未开启带远程调试端口的浏览器，请设为 False，否则会长时间等待连接 9222
CDP_CONNECT_EXISTING = False

# 自定义浏览器路径（可选）
# 如果为空，系统会自动检测 Chrome/Edge 的安装路径
# Windows 示例: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
# macOS 示例: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CUSTOM_BROWSER_PATH = ""

# 是否在 CDP 模式下启用无头模式
# 注意：即使设置为 True，某些反检测功能在无头模式下可能无法正常工作
# 与 HEADLESS 默认一致；命令行 --headless 会同时覆盖 HEADLESS 与 CDP_HEADLESS
CDP_HEADLESS = True

# 浏览器启动超时时间（秒）
BROWSER_LAUNCH_TIMEOUT = 60

# 程序结束时是否自动关闭浏览器
# 设置为 False 可以保持浏览器运行，方便调试
AUTO_CLOSE_BROWSER = True

# Data saving type option configuration, supports: csv, db, json, jsonl, sqlite, excel, postgres. It is best to save to DB, with deduplication function.
SAVE_DATA_OPTION = "jsonl"  # csv or db or json or jsonl or sqlite or excel or postgres

# Data saving path, if not specified by default, it will be saved to the data folder.
SAVE_DATA_PATH = ""

# Browser file configuration cached by the user's browser
USER_DATA_DIR = "%s_user_data_dir"  # %s will be replaced by platform name

# The number of pages to start crawling starts from the first page by default
START_PAGE = 1

# Control the number of crawled videos/posts（创作者主页「全部笔记」时请调大）
CRAWLER_MAX_NOTES_COUNT = 500

# Controlling the number of concurrent crawlers
MAX_CONCURRENCY_NUM = 1

# Whether to enable crawling media mode (including image or video resources), crawling media is not enabled by default
ENABLE_GET_MEIDAS = False

# Whether to enable comment crawling mode. Comment crawling is enabled by default.
ENABLE_GET_COMMENTS = True

# Control the number of crawled first-level comments (single video/post)
CRAWLER_MAX_COMMENTS_COUNT_SINGLENOTES = 10

# Whether to enable the mode of crawling second-level comments. By default, crawling of second-level comments is not enabled.
# If the old version of the project uses db, you need to refer to schema/tables.sql line 287 to add table fields.
ENABLE_GET_SUB_COMMENTS = False

# word cloud related
# Whether to enable generating comment word clouds
ENABLE_GET_WORDCLOUD = False
# Custom words and their groups
# Add rule: xx:yy where xx is a custom-added phrase, and yy is the group name to which the phrase xx is assigned.
CUSTOM_WORDS = {
    "零几": "年份",  # Recognize "zero points" as a whole
    "高频词": "专业术语",  # Example custom words
}

# Deactivate (disabled) word file path
STOP_WORDS_FILE = "./docs/hit_stopwords.txt"

# Chinese font file path
FONT_PATH = "./docs/STZHONGS.TTF"

# Crawl interval
CRAWLER_MAX_SLEEP_SEC = 2

# 是否禁用 SSL 证书验证。仅在使用企业代理、Burp Suite、mitmproxy 等会注入自签名证书的中间人代理时设为 True。
# 警告：禁用 SSL 验证将使所有流量暴露于中间人攻击风险，请勿在生产环境中开启。
DISABLE_SSL_VERIFY = False

from .bilibili_config import *
from .feishu_config import *
from .xhs_config import *
from .dy_config import *
from .ks_config import *
from .weibo_config import *
from .tieba_config import *
from .zhihu_config import *

# 若存在 data/xhs_cookie_string.txt（可由 python tools/export_xhs_cookies.py 生成），自动填入 COOKIES，便于 --lt cookie 复用
try:
    import os as _os_xhs

    _xhs_cookie_fp = _os_xhs.path.normpath(
        _os_xhs.path.join(_os_xhs.path.dirname(_os_xhs.path.abspath(__file__)), "..", "data", "xhs_cookie_string.txt")
    )
    if _os_xhs.path.isfile(_xhs_cookie_fp):
        with open(_xhs_cookie_fp, encoding="utf-8") as _xhs_cf:
            _xhs_cookie_val = _xhs_cf.read().strip()
        if _xhs_cookie_val and not _xhs_cookie_val.startswith("#"):
            COOKIES = _xhs_cookie_val
except OSError:
    pass
