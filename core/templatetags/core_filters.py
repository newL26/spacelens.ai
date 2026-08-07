"""
Core template tags and filters.
"""
from django import template

register = template.Library()


@register.filter(name="split")
def split_filter(value: str, delimiter: str = ",") -> list:
    """Split a string by the given delimiter.

    Usage: {{ "a,b,c"|split:"," }}
    """
    return [item.strip() for item in value.split(delimiter)]
