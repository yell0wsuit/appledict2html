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
