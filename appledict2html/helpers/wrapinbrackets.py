"""Module to add square brackets to content (regional language, etc.)"""

from typing import Optional, Set
from bs4 import BeautifulSoup, Tag


def wrap_class_text_with_brackets(
    soup: BeautifulSoup,
    class_names: Set[str],
    skip_parent_classes: Optional[Set[str]] = None,
):
    """
    Wrap the full rendered content of elements with `class_names` in square brackets `[ ... ]`,
    unless they are inside any ancestor with a class in `skip_parent_classes`.
    """
    if skip_parent_classes is None:
        skip_parent_classes = {"vg"}

    for tag in soup.find_all(True):  # Matches any tag
        if not isinstance(tag, Tag):
            continue

        tag_classes = set(tag.get("class") or [])
        if not tag_classes.intersection(class_names):
            continue

        # Skip if inside a parent with a skip class
        if tag.find_parent(
            lambda parent: isinstance(parent, Tag)
            and not set(parent.get("class") or []).isdisjoint(skip_parent_classes)
        ):
            continue

        # Wrap with brackets
        wrapper = soup.new_tag("span")
        wrapper.append(soup.new_string("["))

        for child in list(tag.contents):  # Copy to avoid mutation during loop
            wrapper.append(child.extract())

        wrapper.append(soup.new_string("]"))
        tag.append(wrapper)
