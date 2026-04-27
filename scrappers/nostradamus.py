import logging
import os
import re
from typing import Any, Dict, Optional

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

from util import MissingCredentialsError, ScrappingError, parse_bytes

logger = logging.getLogger(__name__)

BASE_URL = "https://nostradamus.foo"
SIGNIN_URL = f"{BASE_URL}/sign-in"
SETTINGS_URL = f"{BASE_URL}/settings"


def _clean_text(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    return re.sub(r"\s+", " ", value).strip()


def _extract_number_after_label(text: str, label: str, value_pattern: str) -> Optional[str]:
    m = re.search(rf"{re.escape(label)}\s*[: ]\s*{value_pattern}", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return None


def _parse_stats_from_text(text: str) -> Dict[str, Any]:
    text = _clean_text(text) or ""

    upload = (
        _extract_number_after_label(text, "Uploadé", r"([0-9]+(?:[.,][0-9]+)?\s*[KMGTP]?B)")
        or _extract_number_after_label(text, "Upload", r"([0-9]+(?:[.,][0-9]+)?\s*[KMGTP]?B)")
    )
    download = (
        _extract_number_after_label(text, "Téléchargé", r"([0-9]+(?:[.,][0-9]+)?\s*[KMGTP]?B)")
        or _extract_number_after_label(text, "Download", r"([0-9]+(?:[.,][0-9]+)?\s*[KMGTP]?B)")
    )
    ratio = _extract_number_after_label(text, "Ratio", r"([0-9]+(?:[.,][0-9]+)?)")
    bonus = _extract_number_after_label(text, "Bonus", r"([0-9]+(?:[.,][0-9]+)?)")

    result: Dict[str, Any] = {
        "upload": upload or "N/A",
        "download": download or "N/A",
        "ratio": "N/A",
        "bonus": 0,
        "raw_upload": 0,
        "raw_download": 0,
    }

    if upload:
        try:
            result["raw_upload"] = parse_bytes(upload)
        except Exception:
            pass

    if download:
        try:
            result["raw_download"] = parse_bytes(download)
        except Exception:
            pass

    if ratio:
        try:
            result["ratio"] = float(ratio.replace(",", "."))
        except Exception:
            result["ratio"] = ratio

    if bonus:
        try:
            result["bonus"] = float(bonus.replace(",", "."))
        except Exception:
            result["bonus"] = bonus

    return result


async def _wait_for_real_signin(page) -> None:
    await page.goto(SIGNIN_URL, wait_until="domcontentloaded", timeout=60000)

    for _ in range(24):
        content = await page.content()
        if "Making sure you&#39;re not a bot!" not in content and "private-key-input" in content:
            return
        await page.wait_for_timeout(2500)
        try:
            await page.reload(wait_until="domcontentloaded", timeout=60000)
        except Exception:
            pass

    raise ScrappingError("Nostradamus: anti-bot challenge did not clear")


async def _extract_stats_with_locators(page) -> Dict[str, Any]:
    texts = []

    possible_selectors = [
        "body",
        "main",
        '[href="/settings"]',
        "text=Ratio",
        "text=Uploadé",
        "text=Téléchargé",
        "text=Upload",
        "text=Download",
        "text=Bonus",
    ]

    for sel in possible_selectors:
        try:
            loc = page.locator(sel).first
            if await loc.count() > 0:
                txt = await loc.text_content(timeout=2000)
                if txt:
                    texts.append(txt)
        except Exception:
            pass

    try:
        body_text = await page.locator("body").text_content(timeout=3000)
        if body_text:
            texts.append(body_text)
    except Exception:
        pass

    merged = " ".join(_clean_text(t) or "" for t in texts if t)
    return _parse_stats_from_text(merged)

async def _login_and_fetch(page, private_key: str) -> Dict[str, Any]:
    await _wait_for_real_signin(page)

    key_input = page.locator("#private-key-input")
    await key_input.wait_for(state="visible", timeout=15000)

    await key_input.click()
    await key_input.press("Control+A")
    await key_input.type(private_key, delay=50)
    await key_input.dispatch_event("input")
    await key_input.dispatch_event("change")
    await page.wait_for_timeout(500)

    login_button = page.get_by_role("button", name=re.compile(r"Se connecter", re.I))

    try:
        await login_button.wait_for(state="visible", timeout=10000)
    except PlaywrightTimeoutError:
        login_button = page.locator('button[type="submit"]')

    await key_input.press("Enter")
    await page.wait_for_timeout(2000)

    if "/sign-in" in page.url:
        try:
            if await login_button.is_visible():
                await login_button.click()
                await page.wait_for_timeout(2500)
        except Exception:
            pass

    try:
        await page.wait_for_url(
            re.compile(r"^https://nostradamus\.foo/(?!sign-in).*$"),
            timeout=20000,
        )
    except PlaywrightTimeoutError:
        pass

    if "/sign-in" in page.url:
        try:
            error_text = await page.locator("body").text_content()
        except Exception:
            error_text = ""
        raise ScrappingError(
            "Nostradamus: login failed, still on sign-in page. "
            f"Page text preview: {(error_text or '')[:400]}"
        )

    await page.goto(SETTINGS_URL, wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(3000)

    html = await page.content()
    if "Making sure you&#39;re not a bot!" in html:
        raise ScrappingError("Nostradamus: blocked by anti-bot page after login")

    stats = await _extract_stats_with_locators(page)

    if (
        stats.get("raw_upload", 0) == 0
        and stats.get("raw_download", 0) == 0
        and stats.get("ratio") == "N/A"
    ):
        current_url = page.url
        title = await page.title()
        logger.warning("Nostradamus current URL: %s", current_url)
        logger.warning("Nostradamus page title: %s", title)
        raise ScrappingError("Nostradamus: stats block not found on settings page")

    return stats

async def get_stats(headless: bool = True) -> Dict[str, Any]:
    private_key = (
        os.getenv("NOSTRADAMUS_PRIVATE_KEY")
        or os.getenv("NOSTRADAMUS_API_KEY")
        or os.getenv("NOSTRADAMUS_PRIVATE_TICKET")
    )

    if not private_key:
        raise MissingCredentialsError(
            "Missing NOSTRADAMUS_PRIVATE_KEY (or NOSTRADAMUS_API_KEY) in environment"
        )

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                ],
            )

            context = await browser.new_context(
                locale="fr-FR",
                user_agent=(
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1440, "height": 1024},
            )

            page = await context.new_page()

            try:
                return await _login_and_fetch(page, private_key)
            finally:
                await context.close()
                await browser.close()

    except (MissingCredentialsError, ScrappingError):
        raise
    except Exception as e:
        raise ScrappingError(e)
