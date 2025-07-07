"""Module to process definition blocks inside the Phrases / Phrase verbs"""

from bs4 import BeautifulSoup, Tag
from .class_check import is_class, has_all_classes


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

        xo0.name = "section"
        if original_classes:
            xo0["class"] = original_classes


def convert_xo1_to_list(soup: BeautifulSoup):
    """
    Convert `<span class="x_xo1">` to `<div>` and `<ul>`, and convert
    `<span class="x_xo2">` to `<li>`.
    Preserve all other children (including `.etym.x_xot`).
    """
    for xo1 in soup.find_all("span", class_="x_xo1"):
        if not isinstance(xo1, Tag):
            continue

        subentry_parent = xo1.find_parent(class_="subEntryBlock")
        if not subentry_parent:
            continue

        div = soup.new_tag("div")
        ul = soup.new_tag("ul")
        new_children = []
        ul_insert_index = None

        for i, child in enumerate(list(xo1.contents)):
            if isinstance(child, Tag) and "x_xo2" in (child.get("class") or []):
                li = soup.new_tag("li")
                li.append(child.extract())
                ul.append(li)
                if ul_insert_index is None:
                    ul_insert_index = len(new_children)
            else:
                new_children.append(
                    child.extract() if isinstance(child, Tag) else child
                )

        # Insert <ul> at the position of the first .x_xo2, or at the end if none
        if ul.contents:
            if ul_insert_index is not None:
                new_children.insert(ul_insert_index, ul)
            else:
                new_children.append(ul)

        for child in new_children:
            div.append(child)

        xo1.replace_with(div)


def convert_x_xo_blocks(soup: BeautifulSoup):
    """
    High-level function that applies both `.x_xo0` grouping and `.x_xo1` list
    conversion transformations to the provided BeautifulSoup document.

    This prepares flat span-based HTML for semantic HTML or Markdown export.
    """
    group_xo0_blocks(soup)
    convert_xo1_to_list(soup)


def convert_subsenses_to_list(soup: BeautifulSoup):
    """
    Convert `<span class="msDict x_xo2sub hasSn t_subsense">` elements into `<li>`,
    and wrap them in `<ul>`. Insert the `<ul>` into their parent `.se2 .x_xo2` block.
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
