"""Module to add square brackets to content (regional language, etc.)"""

from typing import Optional, Set
from bs4 import BeautifulSoup, Tag
from bs4.element import NavigableString


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
        # Remove leading/trailing whitespace nodes
        contents = list(tag.contents)
        # Remove leading whitespace nodes
        # Remove leading whitespace nodes
        while contents and (
            str(contents[0]).isspace()
            or (
                getattr(contents[0], "string", None) is not None
                and str(getattr(contents[0], "string")).isspace()
            )
        ):
            contents.pop(0)
        # Remove trailing whitespace nodes
        while contents and (
            str(contents[-1]).isspace()
            or (
                getattr(contents[-1], "string", None) is not None
                and str(getattr(contents[-1], "string")).isspace()
            )
        ):
            contents.pop(-1)

        # Strip leading/trailing whitespace inside first/last NavigableString or Tag with only string
        if contents:
            first = contents[0]
            if isinstance(first, NavigableString):
                first.replace_with(soup.new_string(first.lstrip()))
            elif isinstance(first, Tag) and isinstance(first.string, NavigableString):
                first.string.replace_with(soup.new_string(first.string.lstrip()))

            last = contents[-1]
            if isinstance(last, NavigableString):
                last.replace_with(soup.new_string(last.rstrip()))
            elif isinstance(last, Tag) and isinstance(last.string, NavigableString):
                last.string.replace_with(soup.new_string(last.string.rstrip()))

        # Clear the tag's contents
        tag.clear()

        # Create the wrapper with preserved HTML
        wrapper = soup.new_tag("span")
        wrapper.append(soup.new_string("["))
        for child in contents:
            wrapper.append(child)
        wrapper.append(soup.new_string("] "))
        tag.append(wrapper)
