# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/futianren/KidsTaiChi-MediaCrawler/blob/main/tools/browser_launcher.py
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


import os
import platform
import subprocess
import time
import socket
import signal
import json
import re
from typing import Optional, List, Tuple
import asyncio
from pathlib import Path

import config
from tools import utils


def resolve_chrome_profile_folder(user_data_dir: str) -> str:
    """
    当 user-data-dir 下存在多个 Chrome 资料（无 Default 或需固定其一）时，避免出现「谁在使用 Chrome」选择页。
    优先根据 Local State 里 profile.info_cache 的 active_time 选最近使用的资料夹名。
    """
    if not user_data_dir or not os.path.isdir(user_data_dir):
        return "Default"
    local_state_path = os.path.join(user_data_dir, "Local State")
    if os.path.isfile(local_state_path):
        try:
            with open(local_state_path, encoding="utf-8") as f:
                data = json.load(f)
            info_cache = (data.get("profile") or {}).get("info_cache") or {}
            best_name, best_time = None, -1.0
            for folder_name, meta in info_cache.items():
                if not isinstance(meta, dict):
                    continue
                folder_path = os.path.join(user_data_dir, folder_name)
                if not os.path.isdir(folder_path):
                    continue
                t = float(meta.get("active_time") or -1.0)
                if t > best_time:
                    best_time = t
                    best_name = folder_name
            if best_name:
                return best_name
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            pass
    if os.path.isdir(os.path.join(user_data_dir, "Default")):
        return "Default"
    prof_dirs: List[Tuple[int, str]] = []
    for name in os.listdir(user_data_dir):
        m = re.match(r"^Profile (\d+)$", name)
        if m and os.path.isdir(os.path.join(user_data_dir, name)):
            prof_dirs.append((int(m.group(1)), name))
    prof_dirs.sort()
    if prof_dirs:
        return prof_dirs[-1][1]
    return "Default"


class BrowserLauncher:
    """
    Browser launcher for detecting and launching user's Chrome/Edge browser
    Supports Windows and macOS systems
    """

    def __init__(self):
        self.system = platform.system()
        self.browser_process = None
        self.debug_port = None

    def detect_browser_paths(self) -> List[str]:
        """
        Detect available browser paths in system
        Returns list of browser paths sorted by priority
        """
        paths = []

        if self.system == "Windows":
            # Common Chrome/Edge installation paths on Windows
            possible_paths = [
                # Chrome paths
                os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"),
                os.path.expandvars(r"%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe"),
                os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
                # Edge paths
                os.path.expandvars(r"%PROGRAMFILES%\Microsoft\Edge\Application\msedge.exe"),
                os.path.expandvars(r"%PROGRAMFILES(X86)%\Microsoft\Edge\Application\msedge.exe"),
                # Chrome Beta/Dev/Canary
                os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome Beta\Application\chrome.exe"),
                os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome Dev\Application\chrome.exe"),
                os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome SxS\Application\chrome.exe"),
            ]
        elif self.system == "Darwin":  # macOS
            # Common Chrome/Edge installation paths on macOS
            possible_paths = [
                # Chrome paths
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta",
                "/Applications/Google Chrome Dev.app/Contents/MacOS/Google Chrome Dev",
                "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary",
                # Edge paths
                "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
                "/Applications/Microsoft Edge Beta.app/Contents/MacOS/Microsoft Edge Beta",
                "/Applications/Microsoft Edge Dev.app/Contents/MacOS/Microsoft Edge Dev",
                "/Applications/Microsoft Edge Canary.app/Contents/MacOS/Microsoft Edge Canary",
            ]
        else:
            # Linux and other systems
            possible_paths = [
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable",
                "/usr/bin/google-chrome-beta",
                "/usr/bin/google-chrome-unstable",
                "/usr/bin/chromium-browser",
                "/usr/bin/chromium",
                "/snap/bin/chromium",
                "/usr/bin/microsoft-edge",
                "/usr/bin/microsoft-edge-stable",
                "/usr/bin/microsoft-edge-beta",
                "/usr/bin/microsoft-edge-dev",
            ]

        # Check if path exists and is executable
        for path in possible_paths:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                paths.append(path)

        return paths

    def find_available_port(self, start_port: int = 9222) -> int:
        """
        Find available port
        """
        port = start_port
        while port < start_port + 100:  # Try up to 100 ports
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', port))
                    return port
            except OSError:
                port += 1

        raise RuntimeError(f"Cannot find available port, tried {start_port} to {port-1}")

    def launch_browser(
        self,
        browser_path: str,
        debug_port: int,
        headless: bool = False,
        user_data_dir: Optional[str] = None,
        profile_directory: Optional[str] = None,
    ) -> subprocess.Popen:
        """
        Launch browser process
        """
        args: List[str] = [browser_path]

        # 必须尽早指定资料目录，避免 Chrome 先弹出「谁在使用 Chrome」再被自动化关掉造成闪屏
        if user_data_dir:
            prof = (profile_directory or "").strip() or resolve_chrome_profile_folder(user_data_dir)
            args.append(f"--user-data-dir={user_data_dir}")
            args.append(f"--profile-directory={prof}")
            utils.logger.info(f"[BrowserLauncher] Chrome profile-directory={prof!r} (user-data-dir set)")

        args.extend(
            [
                f"--remote-debugging-port={debug_port}",
                "--remote-debugging-address=0.0.0.0",  # Allow remote access
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-default-apps",
                "--disable-search-engine-choice-screen",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                # TranslateUI 在部分旧版仍存在；ChromeSignin/AccountConsistency 减轻 Chrome 侧登录谷歌引导
                "--disable-features=TranslateUI,ChromeSignin,AccountConsistency,PrivacySandboxSettings4",
                "--disable-ipc-flooding-protection",
                "--disable-hang-monitor",
                "--disable-prompt-on-repost",
                "--disable-sync",
                "--disable-dev-shm-usage",  # Avoid shared memory issues
                "--no-sandbox",  # Disable sandbox in CDP mode
                # Key anti-detection arguments
                "--disable-blink-features=AutomationControlled",  # Disable automation control flag
                "--exclude-switches=enable-automation",  # Exclude automation switch
                "--disable-infobars",  # Disable info bars
            ]
        )
        if getattr(config, "PLAYWRIGHT_IGNORE_SYSTEM_PROXY", True):
            args.append("--no-proxy-server")

        # Headless mode
        if headless:
            args.extend(
                [
                    "--headless=new",  # Use new headless mode
                    "--disable-gpu",
                ]
            )
        else:
            # Extra arguments for non-headless mode
            args.extend(
                [
                    "--start-maximized",  # Maximize window, more like real user
                ]
            )

        utils.logger.info(f"[BrowserLauncher] Launching browser: {browser_path}")
        utils.logger.info(f"[BrowserLauncher] Debug port: {debug_port}")
        utils.logger.info(f"[BrowserLauncher] Headless mode: {headless}")

        try:
            # On Windows, use CREATE_NEW_PROCESS_GROUP to prevent Ctrl+C from affecting subprocess
            if self.system == "Windows":
                process = subprocess.Popen(
                    args,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                process = subprocess.Popen(
                    args,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    preexec_fn=os.setsid  # Create new process group
                )

            self.browser_process = process
            return process

        except Exception as e:
            utils.logger.error(f"[BrowserLauncher] Failed to launch browser: {e}")
            raise

    def wait_for_browser_ready(self, debug_port: int, timeout: int = 30) -> bool:
        """
        Wait for browser to be ready
        """
        utils.logger.info(f"[BrowserLauncher] Waiting for browser to be ready on port {debug_port}...")

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    result = s.connect_ex(('localhost', debug_port))
                    if result == 0:
                        utils.logger.info(f"[BrowserLauncher] Browser is ready on port {debug_port}")
                        return True
            except Exception:
                pass

            time.sleep(0.5)

        utils.logger.error(f"[BrowserLauncher] Browser failed to be ready within {timeout} seconds")
        return False

    def get_browser_info(self, browser_path: str) -> Tuple[str, str]:
        """
        Get browser info (name and version)
        """
        try:
            if "chrome" in browser_path.lower():
                name = "Google Chrome"
            elif "edge" in browser_path.lower() or "msedge" in browser_path.lower():
                name = "Microsoft Edge"
            elif "chromium" in browser_path.lower():
                name = "Chromium"
            else:
                name = "Unknown Browser"

            # Try to get version info
            try:
                result = subprocess.run([browser_path, "--version"],
                                      capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=5)
                version = result.stdout.strip() if result.stdout else "Unknown Version"
            except:
                version = "Unknown Version"

            return name, version

        except Exception:
            return "Unknown Browser", "Unknown Version"

    def cleanup(self):
        """
        Cleanup resources, close browser process
        """
        if not self.browser_process:
            return

        process = self.browser_process

        if process.poll() is not None:
            utils.logger.info("[BrowserLauncher] Browser process already exited, no cleanup needed")
            self.browser_process = None
            return

        utils.logger.info("[BrowserLauncher] Closing browser process...")

        try:
            if self.system == "Windows":
                # First try normal termination
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    utils.logger.warning("[BrowserLauncher] Normal termination timeout, using taskkill to force kill")
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                        capture_output=True,
                        check=False,
                        encoding='utf-8',
                        errors='ignore'
                    )
                    process.wait(timeout=5)
            else:
                pgid = os.getpgid(process.pid)
                try:
                    os.killpg(pgid, signal.SIGTERM)
                except ProcessLookupError:
                    utils.logger.info("[BrowserLauncher] Browser process group does not exist, may have exited")
                else:
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        utils.logger.warning("[BrowserLauncher] Graceful shutdown timeout, sending SIGKILL")
                        os.killpg(pgid, signal.SIGKILL)
                        process.wait(timeout=5)

            utils.logger.info("[BrowserLauncher] Browser process closed")
        except Exception as e:
            utils.logger.warning(f"[BrowserLauncher] Error closing browser process: {e}")
        finally:
            self.browser_process = None
