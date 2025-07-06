"""Module to check if specified class (or class set) is present"""

from bs4 import Tag

def is_class(tag: Tag, class_name: str) -> bool:
    """Return True if the element has the specified class"""
    return tag.has_attr("class") and class_name in tag["class"]


def has_all_classes(tag: Tag, required_classes: set[str]) -> bool:
    """Return True if the element has all the required classes."""
    return (
        tag.name == "span"
        and tag.has_attr("class")
        and required_classes.issubset(set(tag["class"]))
    )
