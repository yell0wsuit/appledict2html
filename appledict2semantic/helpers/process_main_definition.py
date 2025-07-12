"""Module to process the main definition block"""

from typing import cast

from bs4 import BeautifulSoup, Tag
from bs4._typing import _AttributeValue

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


KNOWN_BLOCK_CLASSES = {
    "note": "note_block",
    "etym": "origin_block",
    "x_xdt": "origin_block",
}


def convert_senses_to_list(soup: BeautifulSoup):
    """Convert main senses and subsenses into structured `<ul>`/`<li>` elements, preserving order of all children."""

    for se1 in soup.find_all("span", class_="se1"):
        if not isinstance(se1, Tag):
            continue

        convert_tag(se1, "section")

        # Convert parts of speech
        for pos_block in se1.find_all("span", class_="x_xdh"):
            if isinstance(pos_block, Tag):
                convert_tag(pos_block, "p")

        new_children = []
        sense_li_list = []

        def flush_sense_list():
            nonlocal sense_li_list
            if sense_li_list:
                ul = soup.new_tag("ul")
                for li in sense_li_list:
                    ul.append(li)
                new_children.append(ul)
                sense_li_list = []

        for child in list(se1.contents):
            if isinstance(child, Tag):
                child_classes = set(child.get("class") or [])
                # Check for t_core or t_subsense (main senses)
                if (
                    "t_core" in child_classes
                    or "t_subsense" in child_classes
                    or (
                        child.name == "span"
                        and set(child.get("class") or []) >= {"se2", "x_xd1", "hasSn"}
                    )
                ):
                    convert_tag(child, "li")
                    # Move t_first and subsenses into li as in process_se2_blocks
                    t_first = child.find(
                        lambda t: isinstance(t, Tag)
                        and set(t.get("class") or [])
                        >= {"msDict", "x_xd1sub", "t_first"}
                    )
                    if t_first and isinstance(t_first, Tag):
                        for content in list(t_first.contents):
                            child.append(content)
                        t_first.decompose()
                    # Handle subsenses
                    sub_ul = soup.new_tag("ul")
                    for subsense in child.find_all(
                        lambda t: isinstance(t, Tag)
                        and set(t.get("class") or [])
                        >= {"msDict", "x_xd1sub", "hasSn", "t_subsense"},
                        recursive=False,
                    ):
                        if isinstance(subsense, Tag):
                            li = soup.new_tag("li")
                            li.extend(subsense.contents)
                            subsense.decompose()
                            sub_ul.append(li)
                    if sub_ul.contents:
                        child.append(sub_ul)
                    sense_li_list.append(child)
                else:
                    # If we have collected senses, flush them as a <ul> before this non-sense child
                    flush_sense_list()
                    # Handle known block classes
                    for orig, canonical in KNOWN_BLOCK_CLASSES.items():
                        if orig in child_classes:
                            new_classes = [
                                canonical if c == orig else c for c in child_classes
                            ]
                            child["class"] = cast(_AttributeValue, new_classes)
                            child.name = "section"
                            break
                    new_children.append(child)
            else:
                # If we have collected senses, flush them as a <ul> before this string
                flush_sense_list()
                new_children.append(child)
        # If any senses left at the end, flush them as a <ul>
        flush_sense_list()

        se1.clear()
        for c in new_children:
            se1.append(c)

        process_t_core_blocks(soup, se1)
        process_se2_blocks(soup, se1)
