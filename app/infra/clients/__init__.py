"""Clients package."""

from .amazon_paapi import search_offers as amazon_search
from .rakuten import search_offers as rakuten_search
from .tavily import search_offers as tavily_search
from .yahoo import search_offers as yahoo_search

__all__ = [
    "amazon_search",
    "rakuten_search",
    "tavily_search",
    "yahoo_search",
]
