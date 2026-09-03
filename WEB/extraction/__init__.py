"""
JARVIS AI — Web Content Extraction and Deduplication Package
"""
from WEB.extraction.extractor import WebContentExtractor, ExtractedContent, web_extractor
from WEB.extraction.deduplicator import SourceDeduplicator, source_deduplicator

__all__ = [
    "WebContentExtractor",
    "ExtractedContent",
    "web_extractor",
    "SourceDeduplicator",
    "source_deduplicator",
]
