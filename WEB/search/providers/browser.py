"""
JARVIS AI — Browser Automation Search Provider
Fallback provider using headless browser automation when direct APIs are blocked or unavailable.
"""

from typing import List
from WEB.search.base import BaseSearchProvider, SearchResult


class BrowserSearchProvider(BaseSearchProvider):
    """Fallback search provider utilizing headless browser extraction."""

    def __init__(self):
        super().__init__(name="browser")

    def is_available(self) -> bool:
        try:
            import selenium
            return True
        except ImportError:
            return False

    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        results: List[SearchResult] = []
        if not query or not query.strip():
            return results

        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.common.keys import Keys

            chrome_options = Options()
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--log-level=3")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

            driver = webdriver.Chrome(options=chrome_options)
            try:
                driver.set_page_load_timeout(8)
                driver.get("https://html.duckduckgo.com/html/")
                search_box = driver.find_element(By.NAME, "q")
                search_box.send_keys(query)
                search_box.send_keys(Keys.RETURN)

                elements = driver.find_elements(By.CSS_SELECTOR, ".result")
                for el in elements:
                    if len(results) >= max_results:
                        break
                    try:
                        title_el = el.find_element(By.CSS_SELECTOR, ".result__title a")
                        snippet_el = el.find_element(By.CSS_SELECTOR, ".result__snippet")
                        url = title_el.get_attribute("href")
                        title = title_el.text.strip()
                        snippet = snippet_el.text.strip()
                        if url and title and url.startswith("http"):
                            results.append(
                                SearchResult(
                                    url=url,
                                    title=title,
                                    snippet=snippet,
                                    source_type="webpage",
                                    relevance_score=0.70,
                                )
                            )
                    except Exception:
                        continue
            finally:
                driver.quit()
        except Exception:
            pass

        return results
