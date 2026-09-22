"""Role-criteria knowledge base: category definitions stored as YAML data."""

from .loader import CriteriaError, get_category, get_registry, load_categories
from .schema import Category

__all__ = ["Category", "CriteriaError", "get_category", "get_registry", "load_categories"]
