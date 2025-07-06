"""Module for post-processing the HTML"""

from bs4 import BeautifulSoup, Tag
from bs4.element import NavigableString


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


def convert_usage_note_block(soup: BeautifulSoup):
    """
    Convert `<div class="note x_xo0">` to `<div class="usage_block">`,
    and convert child `<span class="lbl x_blk">` to `<p class="usage_title">`.
    """
    for note_div in soup.find_all("div", class_="note"):
        if not isinstance(note_div, Tag):
            continue

        class_list = note_div.get("class") or []
        if "x_xo0" not in class_list:
            continue

        # Rename the div class
        note_div["class"] = ["usage_block"]

        for span in note_div.find_all("span", recursive=True):
            if not isinstance(span, Tag):
                continue

            classes = set(span.get("class") or [])

            if {"lbl", "x_blk"}.issubset(classes):
                span.name = "p"
                span.attrs = {"class": "usage_title"}


def inject_hw_linebreaks(soup: BeautifulSoup):
    """Append `[linebreaks]` after the headword text in `<span class='hw'>`
    if linebreaks is valid."""

    for span in soup.find_all("span", class_="hw"):
        if not isinstance(span, Tag):
            continue

        linebreaks = span.get("linebreaks")
        if not linebreaks or "|" not in linebreaks or "¦" not in linebreaks:
            continue

        # Find the first NavigableString child (assume it's the headword)
        for i, child in enumerate(span.contents):
            if isinstance(child, NavigableString):
                stripped = child.strip()
                if stripped:
                    span.insert(i + 1, NavigableString(f" [{linebreaks}]"))
                    break


def remove_empty_tags(soup: BeautifulSoup):
    """Remove all empty tags (no content or only whitespace), excluding `<d:index>`."""
    for tag in soup.find_all():
        if (
            isinstance(tag, Tag)
            and tag.name != "d:index"
            and not tag.get_text(strip=True)
            and not tag.find()  # no child tags
        ):
            tag.decompose()


def convert_heading_spans_to_p(soup: BeautifulSoup):
    """Convert `<span class='hg x_xh0'>` to `<p>` and remove its classes."""
    for span in soup.find_all("span"):
        if not isinstance(span, Tag):
            continue
        class_set = set(span.get("class") or [])
        if "hg" in class_set and "x_xh0" in class_set:
            # Create a <p> tag with same content
            p = soup.new_tag("p")

            # Move all children into the new <p>
            while span.contents:
                p.append(span.contents[0])  # moves content instead of copying

            span.replace_with(p)
