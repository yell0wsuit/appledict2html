"""
Convert Apple Dictionary HTML spans into semantic, readable HTML.
This removes the dependency on CSS styles by converting span class names into
appropriate semantic HTML tags and structural markup.
"""

import os
from typing import Optional, Set
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

# Convert multiple classes to semantic tags
COMPOSITE_STYLE_MAP = {
    frozenset(["gp", "ty_hom", "tg_hw"]): {"tag": "sup"},
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
            if not isinstance(xo2, Tag):
                continue

            # Skip if xo2 has no visible content
            if not xo2.get_text(strip=True) and not xo2.find(
                True
            ):  # no text, no children
                xo2.decompose()
                continue

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


CLASS_SETS = {
    "t_core": {"msDict", "x_xd1", "t_core"},
    "t_subsense": {"msDict", "x_xd1", "hasSn", "t_subsense"},
    "se2": {"se2", "x_xd1", "hasSn"},
    "t_first": {"msDict", "x_xd1sub", "t_first"},
    "subsense_in_se2": {"msDict", "x_xd1sub", "hasSn", "t_subsense"},
    "skip_label": {"gp", "x_xdh", "sn", "ty_label", "tg_se2"},
}


def has_classes(tag: Tag, class_key: str) -> bool:
    """Check if a `<span>` tag has all the classes defined in `CLASS_SETS[class_key]`."""
    return tag.name == "span" and CLASS_SETS[class_key].issubset(
        set(tag.get("class") or [])
    )


def convert_tag(tag: Tag, new_name: str):
    """Convert the tag's name unless it's a label span (e.g., sense number)."""
    if has_classes(tag, "skip_label"):
        return
    tag.name = new_name


def create_li_with_contents(soup: BeautifulSoup, tag: Tag) -> Tag:
    """Wrap the inner HTML of `<tag>` in a new `<li>` tag and return it."""
    li = soup.new_tag("li")
    li.append(BeautifulSoup(tag.decode_contents(), "html.parser"))
    return li


def process_t_core_blocks(soup: BeautifulSoup, se1: Tag):
    """Convert all main sense (`t_core`) blocks and their subsenses
    (`t_subsense`) into a nested `<ul>`/`<li>` list structure."""
    t_core_blocks = [
        tag
        for tag in se1.find_all("span")
        if isinstance(tag, Tag) and has_classes(tag, "t_core")
    ]
    if not t_core_blocks:
        return

    ul_core = soup.new_tag("ul")

    for core in t_core_blocks:
        li = create_li_with_contents(soup, core)

        # Handle sibling t_subsense blocks
        sub_ul = soup.new_tag("ul")
        sibling = core.find_next_sibling()
        while sibling and not (
            isinstance(sibling, Tag) and has_classes(sibling, "t_core")
        ):
            next_sibling = sibling.find_next_sibling()
            if isinstance(sibling, Tag) and has_classes(sibling, "t_subsense"):
                sub_ul.append(create_li_with_contents(soup, sibling))
                sibling.decompose()
            sibling = next_sibling

        if sub_ul.contents:
            li.append(sub_ul)

        ul_core.append(li)
        core.decompose()

    se1.append(ul_core)


def process_se2_blocks(soup: BeautifulSoup, se1: Tag):
    """
    Convert second-level sense blocks (se2) into `<li>` elements inside a `<ul>`,
    and nest any `t_first` (definition) or subsense (`x_xd1sub`) elements under them.
    """
    se2_blocks = [
        tag
        for tag in se1.find_all("span", recursive=False)
        if isinstance(tag, Tag) and has_classes(tag, "se2")
    ]
    if not se2_blocks:
        return

    ul_top = soup.new_tag("ul")

    for se2 in se2_blocks:
        convert_tag(se2, "li")

        # Append definition (t_first)
        t_first = se2.find(lambda t: isinstance(t, Tag) and has_classes(t, "t_first"))
        if t_first and isinstance(t_first, Tag):
            for content in list(t_first.contents):
                se2.append(content)
            t_first.decompose()

        # Append nested subsenses
        sub_ul = soup.new_tag("ul")
        for subsense in se2.find_all(
            lambda t: isinstance(t, Tag) and has_classes(t, "subsense_in_se2"),
            recursive=False,
        ):
            if isinstance(subsense, Tag):
                sub_ul.append(create_li_with_contents(soup, subsense))
            subsense.decompose()

        if sub_ul.contents:
            se2.append(sub_ul)

        ul_top.append(se2)

    se1.append(ul_top)


def convert_senses_to_list(soup: BeautifulSoup):
    """Convert main senses and subsenses into structured <ul>/<li> elements"""

    for se1 in soup.find_all("span", class_="se1"):
        if not isinstance(se1, Tag):
            continue

        convert_tag(se1, "div")

        # Convert parts of speech
        for pos_block in se1.find_all("span", class_="x_xdh"):
            if isinstance(pos_block, Tag):
                convert_tag(pos_block, "p")

        process_t_core_blocks(soup, se1)
        process_se2_blocks(soup, se1)


def remove_bullet_spans(soup: BeautifulSoup):
    """Remove all bullet spans since we have `<li>` for that"""
    target_classes = {"gp", "sn", "tg_msDict"}
    for span in soup.find_all("span"):
        if not isinstance(span, Tag):
            continue
        class_set = set(span.get("class") or [])
        if (
            target_classes.issubset(class_set)
            and span.string
            and span.string.strip() == "•"
        ):
            span.decompose()


def convert_origin_block(soup: BeautifulSoup):
    """
    Convert `<div class="etym x_xo0">` to `<div class="origin_block">`,
    and convert child spans as follows:
      - `<span class="x_xo1">` → `<p>`
      - `<span class="gp x_xoLblBlk ty_label tg_etym">` → `<p class="origin_title">`

    Leaves other content unchanged.
    """
    for etym_div in soup.find_all("div", class_="etym"):
        if not isinstance(etym_div, Tag):
            continue

        classes = etym_div.get("class") or []
        if "x_xo0" not in classes:
            continue

        # Change the parent class
        etym_div["class"] = ["origin_block"]

        for child in etym_div.find_all("span", recursive=True):
            if not isinstance(child, Tag):
                continue

            child_classes = set(child.get("class") or [])

            if "x_xo1" in child_classes:
                child.name = "p"
                child.attrs.clear()

            elif {"gp", "x_xoLblBlk", "ty_label", "tg_etym"}.issubset(child_classes):
                child.name = "p"
                child.attrs = {"class": "origin_title"}


def convert_derivatives_block(soup: BeautifulSoup):
    """
    Convert `<div class="subEntryBlock x_xo0 t_derivatives">` to `<div class="derivatives_block">`,
    and transform children:
      - `<span class="gp x_xoLblBlk ty_label tg_subEntryBlock">` → `<p class="derivatives_title">`
      - `<span class="x_xoh">` → `<p>`
    """
    for div in soup.find_all("div", class_="subEntryBlock"):
        if not isinstance(div, Tag):
            continue

        class_list = div.get("class") or []
        if "x_xo0" not in class_list or "t_derivatives" not in class_list:
            continue

        # Replace classes with "derivatives_block"
        div["class"] = ["derivatives_block"]

        for span in div.find_all("span", recursive=True):
            if not isinstance(span, Tag):
                continue

            classes = set(span.get("class") or [])

            if {"gp", "x_xoLblBlk", "ty_label", "tg_subEntryBlock"}.issubset(classes):
                span.name = "p"
                span.attrs = {"class": "derivatives_title"}

            elif "x_xoh" in classes:
                span.name = "p"
                span.attrs.clear()


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
    convert_senses_to_list(soup)
    remove_bullet_spans(soup)
    convert_origin_block(soup)
    convert_derivatives_block(soup)
    return str(soup.prettify())


INPUT_FILENAME = "43957_handle.html"

with open(INPUT_FILENAME, "r", encoding="utf-8") as f:
    html = f.read()

HTML_OUT = process_html(html)

# Append _processed before the .html extension
base, ext = os.path.splitext(INPUT_FILENAME)
OUTPUT_FILENAME = f"{base}_processed{ext}"

with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
    f.write(HTML_OUT)
