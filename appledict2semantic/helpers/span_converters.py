"""Module to convert span classes to semantic HTML tags"""

from bs4 import BeautifulSoup, Tag


# Convert generic span classes (e.g., bold, italic) into semantic HTML tags
STYLE_MAP = {
    "bold": {"tag": "strong"},
    "italic": {"tag": "em"},
    "underline": {"tag": "u"},
    "sup": {"tag": "sup"},
    "sub": {"tag": "sub"},
    "sc": {"tag": "span", "attrs": {"class": "small-caps"}},
    "bi": {"tag": ["em", "strong"]},
    "sui": {"tag": ["sup", "em"]},
    "ini": {"tag": ["sub", "em"]},
}

# Convert Apple-specific span classes into semantic tags (e.g., <i>, <b>, <u>)
APPLE_STYLE_MAP = {
    "sy_underline": {"tag": "u"},
    "str": {"tag": "span", "attrs": {"class": "stress"}},
    "ex": {"tag": "em"},
    "v": {"tag": "strong"},
    "l": {"tag": "strong"},
    "f": {"tag": "strong"},
    "lg": {"tag": "em"},
    "ff": {"tag": ["em", "strong"]},
    "gg": {"tag": "em"},
    "subEnt": {"tag": "sub"},
    "inf": {"tag": "strong"},
    "sy": {"tag": "em"},
    "nu": {"tag": "sup"},
    "dn": {"tag": "sub"},
    "work": {"tag": ["em", "code"]},
}

# Convert multiple classes to semantic tags
COMPOSITE_STYLE_MAP = {
    frozenset(["gp", "ty_hom", "tg_hw"]): {"tag": "sup"},
    frozenset(["gp", "ty_hom", "tg_xr"]): {"tag": "sup"},
}


def convert_span_styles(soup: BeautifulSoup):
    """Convert generic span classes (e.g., `bold`, `italic`) into semantic HTML tags"""

    # Process spans in reverse order to handle nested spans properly
    spans = soup.find_all("span")
    for span in reversed(spans):
        if not isinstance(span, Tag):
            continue  # Skip non-Tag elements (e.g. NavigableString)

        classes = span.get("class") or []
        class_set = frozenset(classes)

        # Composite rules first
        for combo, entry in COMPOSITE_STYLE_MAP.items():
            if combo.issubset(class_set):
                tag_names = (
                    entry["tag"] if isinstance(entry["tag"], list) else [entry["tag"]]
                )
                attrs = entry.get("attrs", {})
                if not isinstance(attrs, dict):
                    attrs = {}
                new = wrap_with_tags(soup, span, tag_names, attrs)
                span.replace_with(new)
                break
        else:
            for cls in classes:
                if cls in STYLE_MAP:
                    entry = STYLE_MAP[cls]
                    tag_names = (
                        entry["tag"]
                        if isinstance(entry["tag"], list)
                        else [entry["tag"]]
                    )
                    attrs = entry.get("attrs", {})
                    new = wrap_with_tags(soup, span, tag_names, attrs)
                    span.replace_with(new)
                    break


def is_inside_eg(span):
    """Check if the span is inside an "eg" class"""
    parent = span.find_parent()
    while parent is not None:
        if isinstance(parent, Tag):
            parent_classes = parent.get("class") or []
            if "eg" in parent_classes:
                return True
            parent = parent.find_parent()
        else:
            break
    return False


def convert_apple_span_styles(soup: BeautifulSoup):
    """Convert Apple-specific span classes into semantic tags (e.g., `<i>`, `<b>`, `<u>`)"""

    # Process spans in reverse order to handle nested spans properly
    spans = soup.find_all("span")
    for span in reversed(spans):
        if not isinstance(span, Tag):
            continue  # Skip non-Tag elements (e.g. NavigableString)

        classes = span.get("class") or []

        # Check if this span has any Apple-specific classes
        apple_classes = [cls for cls in classes if cls in APPLE_STYLE_MAP]

        if apple_classes:
            # Special case: if class is "gg" and inside "eg", use <code> instead of <em>
            if "gg" in apple_classes:
                if is_inside_eg(span):
                    tag_names = ["code"]
                    attrs = {}
                    new = wrap_with_tags_preserving_content(
                        soup, span, tag_names, attrs
                    )
                    if new is not None:
                        span.replace_with(new)
                else:
                    # Not inside "eg", use default mapping
                    entry = APPLE_STYLE_MAP["gg"]
                    tag_names = (
                        entry["tag"]
                        if isinstance(entry["tag"], list)
                        else [entry["tag"]]
                    )
                    attrs = entry.get("attrs", {})
                    new = wrap_with_tags_preserving_content(
                        soup, span, tag_names, attrs
                    )
                    if new is not None:
                        span.replace_with(new)
                continue  # Skip further processing for this span

            # Process only the first matching Apple class
            cls = apple_classes[0]
            entry = APPLE_STYLE_MAP[cls]
            tag_names = (
                entry["tag"] if isinstance(entry["tag"], list) else [entry["tag"]]
            )
            attrs = entry.get("attrs", {})

            # Create new wrapper but preserve all inner content
            new = wrap_with_tags_preserving_content(soup, span, tag_names, attrs)
            if new is not None:
                span.replace_with(new)


def wrap_with_tags(
    soup: BeautifulSoup, element: Tag, tag_names: list[str], attrs: dict | None = None
):
    """Wrap element contents with one or more tags, replacing the original element"""

    if attrs is None:
        attrs = {}

    new = element
    for tag in tag_names:
        wrapped = soup.new_tag(tag, **attrs)
        # Move all contents from the current element to the wrapper
        while new.contents:
            wrapped.append(new.contents[0])
        new = wrapped
    return new


def wrap_with_tags_preserving_content(
    soup: BeautifulSoup, element: Tag, tag_names: list[str], attrs: dict | None = None
):
    """Wrap an element in nested tags while preserving all child tags and structure"""

    if attrs is None:
        attrs = {}

    # Create the wrapper tags from outside to inside
    outermost = None
    current = None

    for tag_name in tag_names:
        wrapper = soup.new_tag(tag_name, **attrs)
        if outermost is None:
            outermost = wrapper
            current = wrapper
        else:
            assert current is not None, "Internal error: current is unexpectedly None"
            current.append(wrapper)
            current = wrapper

    assert current is not None, "Tag list was empty, cannot wrap element"

    # Move all contents from the original element to the innermost wrapper
    while element.contents:
        current.append(element.contents[0])

    return outermost
