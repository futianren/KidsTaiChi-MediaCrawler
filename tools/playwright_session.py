# -*- coding: utf-8 -*-
"""
Playwright session management utilities
"""

from pathlib import Path
from typing import Optional, Tuple

from playwright.async_api import Browser, BrowserContext, BrowserType, Playwright

import config
from tools import utils


def session_path_for_platform(platform: str) -> Path:
    """
    Get the session storage path for a given platform

    Args:
        platform: Platform name (e.g., 'xhs', 'dy', 'ks')

    Returns:
        Path to the session.json file
    """
    return Path(f"cookiesFile/{platform}/session.json")


async def attach_chromium_browser(
    playwright: Playwright,
    cdp_url: str,
    user_agent: Optional[str] = None,
    proxy: Optional[dict] = None,
    state_path: Optional[Path] = None,
) -> Tuple[Browser, BrowserContext]:
    """
    Attach to an existing Chromium browser via CDP

    Args:
        playwright: Playwright instance
        cdp_url: CDP endpoint URL
        user_agent: User agent string
        proxy: Proxy configuration
        state_path: Path to storage state file

    Returns:
        Tuple of (Browser, BrowserContext)
    """
    browser = await playwright.chromium.connect_over_cdp(cdp_url)

    context_options = {}
    if user_agent:
        context_options["user_agent"] = user_agent
    if proxy:
        context_options["proxy"] = proxy
    if state_path and state_path.exists():
        context_options["storage_state"] = str(state_path)

    if browser.contexts:
        context = browser.contexts[0]
    else:
        context = await browser.new_context(**context_options)

    return browser, context


async def finalize_standard_playwright(
    browser_context: BrowserContext,
    state_path: Optional[Path] = None,
    close_browser: bool = True,
) -> None:
    """
    Finalize Playwright session and optionally save state

    Args:
        browser_context: Browser context to finalize
        state_path: Path to save storage state
        close_browser: Whether to close the browser
    """
    try:
        if state_path and config.SAVE_LOGIN_STATE:
            state_path.parent.mkdir(parents=True, exist_ok=True)
            await browser_context.storage_state(path=str(state_path))
            utils.logger.info(f"[playwright_session] Saved storage state to {state_path}")
    except Exception as e:
        utils.logger.warning(f"[playwright_session] Failed to save storage state: {e}")

    if close_browser:
        try:
            await browser_context.close()
        except Exception as e:
            error_msg = str(e).lower()
            if "closed" not in error_msg and "disconnected" not in error_msg:
                utils.logger.warning(f"[playwright_session] Error closing browser context: {e}")
