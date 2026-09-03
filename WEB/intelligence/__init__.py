"""
JARVIS AI — Web Intelligence & Source Analysis Package
"""
from WEB.intelligence.source_scorer import SourceQualityScorer, SourceQualityScore, source_scorer
from WEB.intelligence.recency import RecencyAnalyzer, recency_analyzer
from WEB.intelligence.fact_extractor import FactExtractor, ExtractedClaim, fact_extractor
from WEB.intelligence.cross_checker import CrossChecker, CrossCheckResult, cross_checker
from WEB.intelligence.comparator import ComparisonEngine, ComparisonResult, comparison_engine
from WEB.intelligence.citations import CitationManager, Citation, citation_manager

__all__ = [
    "SourceQualityScorer",
    "SourceQualityScore",
    "source_scorer",
    "RecencyAnalyzer",
    "recency_analyzer",
    "FactExtractor",
    "ExtractedClaim",
    "fact_extractor",
    "CrossChecker",
    "CrossCheckResult",
    "cross_checker",
    "ComparisonEngine",
    "ComparisonResult",
    "comparison_engine",
    "CitationManager",
    "Citation",
    "citation_manager",
]
