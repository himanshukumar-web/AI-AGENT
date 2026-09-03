"""
JARVIS AI — Safe Web Content Extractor
Extracts clean, readable page text, headings, metadata, and tables while eliminating noise.
"""

from dataclasses import dataclass, field
import re
from typing import Any, Dict, List, Optional
import requests
from bs4 import BeautifulSoup


@dataclass
class ExtractedContent:
    """Structured result of cleaned web content extraction."""
    url: str
    title: str
    text: str
    headings: List[str] = field(default_factory=list)
    tables: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    word_count: int = 0
    publication_date: Optional[str] = None
    success: bool = True
    error: Optional[str] = None


class WebContentExtractor:
    """Safe, rate-conscious content extractor."""

    UNWANTED_TAGS = [
        "script", "style", "nav", "footer", "header", "aside",
        "noscript", "iframe", "svg", "form", "button", "dialog",
        "select", "option", "canvas", "video", "audio"
    ]

    UNWANTED_CLASSES_OR_IDS = [
        "cookie", "banner", "ad-", "ads-", "advert", "sponsor",
        "sidebar", "menu", "nav", "social-share", "newsletter",
        "popup", "modal", "disclaimer", "comments", "feedback"
    ]

    def __init__(self, timeout: float = 6.0, max_chars: int = 40000):
        self.timeout = timeout
        self.max_chars = max_chars
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })

    def fetch_and_extract(self, url: str) -> ExtractedContent:
        """Fetch URL content over HTTP and extract structured readable content."""
        if not url or not url.startswith(("http://", "https://")):
            return ExtractedContent(url=url, title="", text="", success=False, error="Invalid URL")

        try:
            resp = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            if resp.status_code != 200:
                return ExtractedContent(
                    url=url,
                    title="",
                    text="",
                    success=False,
                    error=f"HTTP {resp.status_code}: {resp.reason}",
                )

            # Validate Content-Type
            content_type = resp.headers.get("Content-Type", "").lower()
            if "text/html" not in content_type and "application/xhtml" not in content_type:
                return ExtractedContent(
                    url=url,
                    title="",
                    text="",
                    success=False,
                    error=f"Unsupported Content-Type: {content_type}",
                )

            return self.extract_from_html(resp.text, url=resp.url)

        except requests.Timeout:
            return ExtractedContent(url=url, title="", text="", success=False, error="Request timed out")
        except Exception as e:
            return ExtractedContent(url=url, title="", text="", success=False, error=str(e))

    def extract_from_html(self, html: str, url: str = "") -> ExtractedContent:
        """Parse raw HTML string and extract clean text, headings, metadata, and tables."""
        if not html or not html.strip():
            return ExtractedContent(url=url, title="", text="", success=False, error="Empty HTML")

        try:
            soup = BeautifulSoup(html, "html.parser")

            # 1. Extract metadata before stripping tags
            metadata = {}
            title = ""
            pub_date = None

            # Title
            og_title = soup.find("meta", property="og:title")
            if og_title and og_title.get("content"):
                title = og_title["content"].strip()
            elif soup.title and soup.title.string:
                title = soup.title.string.strip()
            elif soup.find("h1"):
                title = soup.find("h1").get_text().strip()

            # Description
            meta_desc = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", property="og:description")
            if meta_desc and meta_desc.get("content"):
                metadata["description"] = meta_desc["content"].strip()

            # Publication date
            date_meta = (
                soup.find("meta", property="article:published_time")
                or soup.find("meta", attrs={"name": "date"})
                or soup.find("meta", attrs={"name": "pubdate"})
                or soup.find("meta", attrs={"name": "publication_date"})
            )
            if date_meta and date_meta.get("content"):
                pub_date = date_meta["content"].strip()
            else:
                time_el = soup.find("time")
                if time_el:
                    pub_date = time_el.get("datetime") or time_el.get_text().strip()

            # 2. Extract and format tables into Markdown
            tables_md = []
            for t in soup.find_all("table"):
                table_md = self._table_to_markdown(t)
                if table_md:
                    tables_md.append(table_md)

            # 3. Strip unwanted tags
            for tag in self.UNWANTED_TAGS:
                for el in soup.find_all(tag):
                    el.decompose()

            # Strip noisy classes / IDs
            for el in soup.find_all(True):
                class_str = " ".join(el.get("class", [])).lower()
                id_str = str(el.get("id", "")).lower()
                if any(bad in class_str or bad in id_str for bad in self.UNWANTED_CLASSES_OR_IDS):
                    el.decompose()

            # 4. Extract headings
            headings = []
            for h in soup.find_all(["h1", "h2", "h3"]):
                htext = h.get_text().strip()
                if htext and len(htext) > 3 and htext not in headings:
                    headings.append(htext)

            # 5. Extract readable body text
            # Prefer article, main, or content containers if available
            main_container = soup.find("article") or soup.find("main") or soup.find(attrs={"role": "main"})
            target_scope = main_container if main_container else soup

            text_blocks = []
            for p in target_scope.find_all(["p", "li", "h1", "h2", "h3", "h4", "pre", "blockquote"]):
                line = p.get_text().strip()
                if len(line) > 20:  # Filter out one-word breadcrumbs
                    text_blocks.append(line)

            full_text = "\n\n".join(text_blocks)
            full_text = re.sub(r"\n{3,}", "\n\n", full_text).strip()

            if len(full_text) > self.max_chars:
                full_text = full_text[:self.max_chars] + "\n\n[Content truncated for length]"

            word_count = len(full_text.split())

            return ExtractedContent(
                url=url,
                title=title or "Untitled Page",
                text=full_text,
                headings=headings,
                tables=tables_md,
                metadata=metadata,
                word_count=word_count,
                publication_date=pub_date,
                success=bool(full_text),
            )

        except Exception as e:
            return ExtractedContent(url=url, title="", text="", success=False, error=str(e))

    def _table_to_markdown(self, table_el) -> str:
        """Convert an HTML table into a clean markdown table string."""
        rows = table_el.find_all("tr")
        if not rows:
            return ""

        grid = []
        for r in rows:
            cols = [c.get_text().strip().replace("\n", " ") for c in r.find_all(["th", "td"])]
            if cols:
                grid.append(cols)

        if not grid:
            return ""

        max_cols = max(len(row) for row in grid)
        # Pad shorter rows
        for row in grid:
            while len(row) < max_cols:
                row.append("")

        lines = []
        # Header row
        header = grid[0]
        lines.append("| " + " | ".join(header) + " |")
        lines.append("| " + " | ".join(["---"] * max_cols) + " |")

        for row in grid[1:]:
            lines.append("| " + " | ".join(row) + " |")

        return "\n".join(lines)


# Global singleton instance
web_extractor = WebContentExtractor()
