from mcp.server.fastmcp import FastMCP
from playwright.async_api import TimeoutError as PlaywrightTimeout
from playwright.async_api import async_playwright

mcp = FastMCP("weather-Israel")

FORECAST_URL = "https://www.weather2day.co.il/forecast"

_playwright = None
_browser = None
_page = None


def _media_state() -> str:
    return "open" if _browser and _page else "closed"


def _clean_page_text(text: str) -> str:
    """Collapse a raw page-text dump into non-empty, whitespace-trimmed lines."""
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


async def _ensure_page() -> object:
    global _playwright, _browser, _page

    if _page is not None:
        return _page

    _playwright = await async_playwright().start()
    _browser = await _playwright.chromium.launch(headless=False)
    _page = await _browser.new_page()
    return _page


async def _find_first_visible_suggestion(page: object):
    suggestion_selectors = [
        '#city_search_forecastautocomplete-list > div',
        '#city_search_forecastautocomplete-list div',
        '#MenuToggle li',
    ]

    for selector in suggestion_selectors:
        suggestions = await page.query_selector_all(selector)
        for suggestion in suggestions:
            visible = await suggestion.evaluate('(el) => el.offsetParent !== null')
            if visible:
                return suggestion
    return None


@mcp.tool()
async def open_weather_forecast_israel() -> str:
    """Open the Israeli weather forecast site in the browser."""
    page = await _ensure_page()
    try:
        await page.goto(FORECAST_URL, timeout=60000)
        return f"Opened Israel weather forecast page: {page.url}"
    except PlaywrightTimeout:
        return "Timeout while opening the Israel weather forecast page."


@mcp.tool()
async def enter_weather_forecast_city_israel(city: str) -> str:
    """Enter a city name into the Israel weather forecast search field."""
    page = await _ensure_page()
    try:
        await page.wait_for_selector('#city_search_forecast', timeout=15000)
        await page.fill('#city_search_forecast', city)
        await page.wait_for_timeout(1500)
        await page.wait_for_selector('#MenuToggle li', timeout=15000)
        return f"Entered city '{city}' into the Israeli weather search field."
    except PlaywrightTimeout:
        return "Timeout while entering the city name into the Israeli weather search field."


@mcp.tool()
async def select_weather_forecast_city_israel() -> str:
    """Select the first matching city suggestion on the Israeli weather site."""
    page = await _ensure_page()
    try:
        await page.wait_for_selector('#city_search_forecastautocomplete-list', timeout=15000)
        suggestion = await _find_first_visible_suggestion(page)
        if suggestion is None:
            return "No visible city suggestion was found."

        try:
            await suggestion.click()
        except Exception:
            # Fallback to keyboard navigation if the element is not clickable directly.
            await page.keyboard.press('ArrowDown')
            await page.keyboard.press('Enter')

        await page.wait_for_load_state('networkidle', timeout=20000)
        title = await page.title()
        return f"Selected the first suggested city. Current page title: {title}. URL: {page.url}"
    except PlaywrightTimeout:
        return "Timeout while selecting the first city suggestion."


@mcp.tool()
async def read_weather_forecast_content_israel() -> str:
    """Read and return the cleaned, visible text content of the currently open
    Israeli weather forecast page, so the model can answer the user's question
    directly from the page content instead of only navigating it."""
    page = await _ensure_page()
    try:
        await page.wait_for_load_state('networkidle', timeout=20000)
        raw_text = await page.inner_text('body')
        cleaned = _clean_page_text(raw_text)
        if not cleaned:
            return "No readable content was found on the page."
        return cleaned
    except PlaywrightTimeout:
        return "Timeout while reading the weather forecast page content."


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

