"""
Convert Apple Dictionary HTML spans into semantic, readable HTML.
This removes the dependency on CSS styles by converting span class names into
appropriate semantic HTML tags and structural markup.
"""

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
}

# Convert multiple classes to semantic tags. Currently left as comment due to bugs,
# will revise or remove if needed.
COMPOSITE_STYLE_MAP = {
    # frozenset(["l", "x_xoh"]): {"tag": "b"},
    # frozenset(["str", "t_l"]): {"tag": "u"},
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


def wrap_class_text_with_brackets(soup: BeautifulSoup, class_names: set[str]):
    """Wrap the full rendered content of elements with
    specified classes in square brackets `[ ... ]`"""
    for tag in soup.find_all(True):  # Matches any tag
        if not isinstance(tag, Tag):
            continue

        classes = set(tag.get("class") or [])
        if not classes.intersection(class_names):
            continue

        # Create new wrapper tag
        wrapper = soup.new_tag("span")
        wrapper.append(soup.new_string("["))

        # Move original children into the wrapper
        for child in list(
            tag.contents
        ):  # list() to avoid modification during iteration
            wrapper.append(child.extract())

        wrapper.append(soup.new_string("]"))
        tag.append(wrapper)


def is_class(tag: Tag, class_name: str) -> bool:
    """Return True if the element has the specified class"""
    return tag.has_attr("class") and class_name in tag["class"]


def group_xo0_blocks(soup: BeautifulSoup):
    """
    Group `.x_xo0` spans with their following siblings (until the next `.x_xo0`)
    and convert them into `<div>` blocks while preserving their original classes.

    This helps structure flat span-based data into meaningful grouped sections.
    """

    for xo0 in soup.find_all("span", class_="x_xo0"):
        if not isinstance(xo0, Tag):
            continue

        original_classes = xo0.get("class")

        siblings = []
        sib = xo0.find_next_sibling()
        while sib:
            if not isinstance(sib, Tag):
                sib = sib.find_next_sibling()
                continue
            if is_class(sib, "x_xo0"):
                break
            next_sib = sib.find_next_sibling()
            siblings.append(sib)
            sib.extract()
            sib = next_sib

        for child in siblings:
            xo0.append(child)

        xo0.name = "div"
        if original_classes:
            xo0["class"] = original_classes


def convert_xo1_to_list(soup: BeautifulSoup):
    """
    Convert `.x_xo1` spans inside `.subEntryBlock` into `<div class="subEntry">` blocks.
    Each `.x_xo2` child becomes a `<li>` inside a nested `<ul>`.

    Outside `.subEntryBlock`, `.x_xo1` spans are left unchanged.
    """
    for xo1 in soup.find_all("span", class_="x_xo1"):
        if not isinstance(xo1, Tag):
            continue

        subentry_parent = xo1.find_parent(class_="subEntryBlock")
        if not subentry_parent:
            continue

        div = soup.new_tag("div")

        # Extract the label (x_xoh or l)
        xoh = xo1.find("span", class_="x_xoh") or xo1.find("span", class_="l")
        if xoh:
            div.append(xoh.extract())
        else:
            div.string = xo1.get_text(strip=True)

        # Create nested list of .x_xo2 spans
        nested_ul = soup.new_tag("ul")
        for xo2 in xo1.find_all("span", class_="x_xo2", recursive=False):
            li2 = soup.new_tag("li")
            li2.append(xo2.extract())
            nested_ul.append(li2)

        if nested_ul.contents:
            div.append(nested_ul)

        xo1.replace_with(div)


def convert_x_xo_blocks(soup: BeautifulSoup):
    """
    High-level function that applies both `.x_xo0` grouping and `.x_xo1` list
    conversion transformations to the provided BeautifulSoup document.

    This prepares flat span-based HTML for semantic HTML or Markdown export.
    """
    group_xo0_blocks(soup)
    convert_xo1_to_list(soup)


def has_all_classes(tag: Tag, required_classes: set[str]) -> bool:
    """Return True if the element has all the required classes."""
    return (
        tag.name == "span"
        and tag.has_attr("class")
        and required_classes.issubset(set(tag["class"]))
    )


def convert_subsenses_to_list(soup: BeautifulSoup):
    """
    Convert <span class="msDict x_xo2sub hasSn t_subsense"> elements into <li>,
    and wrap them in <ul>. Insert the <ul> into their parent .se2 .x_xo2 block.
    """

    required_classes = {"msDict", "x_xo2sub", "hasSn", "t_subsense"}

    for entry in soup.find_all("span", class_="se2"):
        if not isinstance(entry, Tag):
            continue

        subsenses = [
            tag
            for tag in entry.find_all(recursive=False)
            if isinstance(tag, Tag) and has_all_classes(tag, required_classes)
        ]

        if not subsenses:
            continue

        ul = soup.new_tag("ul")

        for subsense in subsenses:
            li = soup.new_tag("li")
            li.extend(subsense.contents)
            subsense.decompose()
            ul.append(li)

        # Find last "t_first" msDict to insert after
        for child in entry.contents:
            if isinstance(child, Tag):
                child_classes = set(child.get("class") or [])
                if child_classes >= {"msDict", "x_xo2sub", "t_first"}:
                    child.insert_after(ul)
                    break
        else:
            # Fallback: append at end
            entry.append(ul)


# --- Full processing pipeline ---
def process_html(result: str) -> str:
    """Main processing pipeline: applies all span-to-tag conversions
    and structural transformations"""
    soup = BeautifulSoup(result, "lxml")
    convert_x_xo_blocks(soup)
    convert_span_styles(soup)
    wrap_class_text_with_brackets(soup, {"lg"})
    convert_apple_span_styles(soup)
    convert_subsenses_to_list(soup)
    return str(soup.prettify())


with open("block_test.html", "r", encoding="utf-8") as f:
    html = f.read()

HTML_OUT = process_html(html)
with open("block_test_processed.html", "w", encoding="utf-8") as f:
    f.write(HTML_OUT)
