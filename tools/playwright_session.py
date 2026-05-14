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
    browser_type: BrowserType,
    headless: bool = False,
    playwright_proxy: Optional[dict] = None,
    user_agent: Optional[str] = None,
    viewport: Optional[dict] = None,
    storage_state_path: Optional[Path] = None,
) -> Tuple[Browser, BrowserContext]:
    """
    Launch a Chromium browser with Playwright

    Args:
        browser_type: Playwright browser type (chromium)
        headless: Whether to run in headless mode
        playwright_proxy: Proxy configuration
        user_agent: User agent string
        viewport: Viewport size dict with width and height
        storage_state_path: Path to storage state file

    Returns:
        Tuple of (Browser, BrowserContext)
    """
    launch_options = {
        "headless": headless,
    }
    if playwright_proxy:
        launch_options["proxy"] = playwright_proxy

    browser = await browser_type.launch(**launch_options)

    context_options = {}
    if user_agent:
        context_options["user_agent"] = user_agent
    if viewport:
        context_options["viewport"] = viewport
    if storage_state_path and storage_state_path.exists():
        context_options["storage_state"] = str(storage_state_path)

    context = await browser.new_context(**context_options)

    return browser, context


async def finalize_standard_playwright(
    use_cdp: bool = False,
    save_login_state: bool = False,
    persist_ok: bool = False,
    browser_context: Optional[BrowserContext] = None,
    playwright_browser: Optional[Browser] = None,
    platform: str = "",
    log = None,
    state_path: Optional[Path] = None,
    close_browser: bool = True,
) -> None:
    """
    Finalize Playwright session and optionally save state

    Args:
        use_cdp: Whether CDP mode is being used
        save_login_state: Whether to save login state
        persist_ok: Whether persistence was successful
        browser_context: Browser context to finalize
        playwright_browser: Browser instance
        platform: Platform name
        log: Logger instance
        state_path: Path to save storage state (overrides platform-based path)
        close_browser: Whether to close the browser
    """
    if not browser_context:
        return

    logger = log if log else utils.logger

    try:
        if save_login_state and persist_ok:
            if not state_path:
                state_path = session_path_for_platform(platform) if platform else None

            if state_path:
                state_path.parent.mkdir(parents=True, exist_ok=True)
                await browser_context.storage_state(path=str(state_path))
                logger.info(f"[playwright_session] Saved storage state to {state_path}")
    except Exception as e:
        logger.warning(f"[playwright_session] Failed to save storage state: {e}")

    if close_browser and not use_cdp:
        try:
            if browser_context:
                await browser_context.close()
            if playwright_browser:
                await playwright_browser.close()
        except Exception as e:
            error_msg = str(e).lower()
            if "closed" not in error_msg and "disconnected" not in error_msg:
                logger.warning(f"[playwright_session] Error closing browser: {e}")

