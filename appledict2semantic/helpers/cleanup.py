"""Module for post-processing the HTML"""

from typing import cast
from bs4 import BeautifulSoup, Tag
from bs4.element import NavigableString
from bs4._typing import _AttributeValue


def cleanup_stuff(soup: BeautifulSoup):
    """Cleanup stuff"""
    remove_bullet_spans(soup)
    convert_inline_origin_block(soup)
    convert_origin_block(soup)
    convert_derivatives_block(soup)
    convert_usage_note_block(soup)
    inject_hw_linebreaks(soup)
    remove_empty_tags(soup)
    convert_heading_spans_to_p(soup)
    convert_phrasal_verbs_block(soup)
    convert_phrasal_block(soup)
    convert_note_block(soup)
    convert_phrase_origin_to_p(soup)
    convert_etym_label_to_origin_title(soup)
    unwrap_span(soup)
    clean_attributes(soup)
    ensure_space_after_tags(soup, ["strong", "em"])
    strip_title_whitespace(soup)


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
    Convert `<section class="etym x_xo0">` to `<section class="origin_block">`,
    and convert child spans as follows:
      - `<span class="x_xo1">` → `<p>`
      - `<span class="gp x_xoLblBlk ty_label tg_etym">` → `<p class="origin_title">`

    Leaves other content unchanged.
    """
    for etym_div in soup.find_all("section", class_="etym"):
        if not isinstance(etym_div, Tag):
            continue

        classes = etym_div.get("class") or []
        if "x_xo0" not in classes:
            continue

        # Change the parent class
        etym_div["class"] = cast(_AttributeValue, ["origin_block"])

        for child in etym_div.find_all("span", recursive=True):
            if not isinstance(child, Tag):
                continue

            child_classes = set(child.get("class") or [])

            if "x_xo1" in child_classes:
                child.name = "p"
                child.attrs.clear()

            elif {"gp", "x_xoLblBlk", "ty_label", "tg_etym"}.issubset(child_classes):
                child.name = "p"
                child["class"] = cast(_AttributeValue, ["origin_title"])


def convert_derivatives_block(soup: BeautifulSoup):
    """
    Convert `<section class="subEntryBlock x_xo0 t_derivatives">` to `<section class="derivatives_block">`,
    and transform children:
      - `<span class="gp x_xoLblBlk ty_label tg_subEntryBlock">` → `<p class="derivatives_title">`
      - `<span class="x_xoh">` → `<p>`
    """
    for div in soup.find_all("section", class_="subEntryBlock"):
        if not isinstance(div, Tag):
            continue

        class_list = div.get("class") or []
        if "x_xo0" not in class_list or "t_derivatives" not in class_list:
            continue

        # Replace classes with "derivatives_block"
        div["class"] = cast(_AttributeValue, ["derivatives_block"])

        for span in div.find_all("span", recursive=True):
            if not isinstance(span, Tag):
                continue

            classes = set(span.get("class") or [])

            if {"gp", "x_xoLblBlk", "ty_label", "tg_subEntryBlock"}.issubset(classes):
                span.name = "p"
                span["class"] = cast(_AttributeValue, ["derivatives_title"])

            elif "x_xoh" in classes:
                span.name = "p"
                span.attrs.clear()


def convert_usage_note_block(soup: BeautifulSoup):
    """
    Convert `<section class="note x_xo0">` to `<section class="usage_block">`,
    and convert child `<span class="lbl x_blk">` to `<p class="usage_title">`.
    """
    for note_div in soup.find_all("section", class_="note"):
        if not isinstance(note_div, Tag):
            continue

        class_list = note_div.get("class") or []
        if "x_xo0" not in class_list:
            continue

        # Rename the div class
        note_div["class"] = cast(_AttributeValue, ["usage_block"])

        for span in note_div.find_all("span", recursive=True):
            if not isinstance(span, Tag):
                continue

            classes = set(span.get("class") or [])

            if {"lbl", "x_blk"}.issubset(classes):
                span.name = "p"
                span["class"] = cast(_AttributeValue, ["usage_title"])


def convert_note_block(soup: BeautifulSoup):
    """
    Convert `<section class="note">` to `<section class="note_block">`.
    """
    for note_span in soup.find_all("span", class_="note"):
        if not isinstance(note_span, Tag):
            continue

        note_span["class"] = cast(_AttributeValue, ["note_block"])
        note_span.name = "section"


def convert_phrase_origin_to_p(soup: BeautifulSoup):
    """
    Convert <span class="etym x_xo3"> to <p> and remove its classes.
    """
    for span in soup.find_all("span", class_="etym"):
        if not isinstance(span, Tag):
            continue
        class_set = set(span.get("class") or [])
        if "x_xo3" in class_set:
            span.name = "p"
            span.attrs.clear()


def convert_inline_origin_block(soup: BeautifulSoup):
    """
    Convert `<span class="etym x_xot">` to `<section class="origin_block origin_inline">` and
    `<span class="gp ty_label tg_etym">` to `<p class="origin_title">`.
    """
    # Find all etym spans with x_xot class (these are inline origin blocks)
    etym_spans = soup.find_all("span", class_="etym")

    for span in etym_spans:
        if not isinstance(span, Tag):
            continue
        class_set = set(span.get("class") or [])
        if "x_xot" in class_set:
            # Convert the main span to section
            span.name = "section"
            span["class"] = cast(_AttributeValue, ["origin_block", "origin_inline"])

            # Convert the title span within this section
            for inner_span in span.find_all("span"):
                if not isinstance(inner_span, Tag):
                    continue
                inner_class_set = set(inner_span.get("class") or [])
                if {"gp", "ty_label", "tg_etym"}.issubset(inner_class_set):
                    inner_span.name = "p"
                    inner_span["class"] = cast(_AttributeValue, ["origin_title"])

            # Remove other attributes after processing children
            for attr in ["id", "role"]:
                if attr in span.attrs:
                    del span.attrs[attr]


def convert_etym_label_to_origin_title(soup: BeautifulSoup):
    """
    Convert <span class="gp ty_label tg_etym"> to <p class="origin_title">.
    """
    for span in soup.find_all("span"):
        if not isinstance(span, Tag):
            continue
        classes = set(span.get("class") or [])
        if {"gp", "ty_label", "tg_etym"}.issubset(classes):
            span.name = "p"
            span["class"] = cast(_AttributeValue, ["origin_title"])


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
    """Recursively remove all empty tags (no content or only whitespace), excluding <d:index>."""

    def is_effectively_empty(tag):
        # Only check Tag, not NavigableString
        if not isinstance(tag, Tag):
            return True
        if tag.name == "d:index":
            return False  # Never remove <d:index>
        # If tag has text, not empty
        if tag.get_text(strip=True):
            return False
        # If tag has any non-empty child, not empty
        for child in tag.find_all(recursive=False):
            if not is_effectively_empty(child):
                return False
        return True

    # Work from the bottom up to ensure parents are checked after children
    for tag in reversed(list(soup.find_all())):
        if isinstance(tag, Tag) and tag.name != "d:index" and is_effectively_empty(tag):
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


def convert_phrasal_verbs_block(soup: BeautifulSoup):
    """
    Convert `<section class="subEntryBlock x_xo0 t_phrasalVerbs">` to
    `<section class="phrasalverbs_block">`, and transform children:
      - `<span class="gp x_xoLblBlk ty_label tg_subEntryBlock">` → `<p class="phrasalverbs_title">`
    """
    for div in soup.find_all("section", class_="subEntryBlock"):
        if not isinstance(div, Tag):
            continue

        class_list = div.get("class") or []
        if "x_xo0" not in class_list or "t_phrasalVerbs" not in class_list:
            continue

        # Replace classes with "phrasalverbs_block"
        div["class"] = cast(_AttributeValue, ["phrasalverbs_block"])

        for span in div.find_all("span", recursive=True):
            if not isinstance(span, Tag):
                continue

            classes = set(span.get("class") or [])

            if {"gp", "x_xoLblBlk", "ty_label", "tg_subEntryBlock"}.issubset(classes):
                span.name = "p"
                span["class"] = cast(_AttributeValue, ["phrasalverbs_title"])


def convert_phrasal_block(soup: BeautifulSoup):
    """
    Convert `<section class="subEntryBlock x_xo0 t_phrases">` to
    `<section class="phrases_block">`, and transform children:
      - `<span class="gp x_xoLblBlk ty_label tg_subEntryBlock">` → `<p class="phrases_title">`
    """
    for div in soup.find_all("section", class_="subEntryBlock"):
        if not isinstance(div, Tag):
            continue

        class_list = div.get("class") or []
        if "x_xo0" not in class_list or "t_phrases" not in class_list:
            continue

        # Replace classes with "phrasalverbs_block"
        div["class"] = cast(_AttributeValue, ["phrases_block"])

        for span in div.find_all("span", recursive=True):
            if not isinstance(span, Tag):
                continue

            classes = set(span.get("class") or [])

            if {"gp", "x_xoLblBlk", "ty_label", "tg_subEntryBlock"}.issubset(classes):
                span.name = "p"
                span["class"] = cast(_AttributeValue, ["phrases_title"])


def unwrap_span(soup: BeautifulSoup):
    """
    Unwrap leftover tags to clean up the HTML.
    """
    for span in soup.find_all("span"):
        if not isinstance(span, Tag):
            continue
        span.unwrap()

    for d_prn in soup.find_all("d:prn"):
        d_prn.decompose()

    for d_def in soup.find_all("d:def"):
        d_def.decompose()

    for d_pos in soup.find_all("d:pos"):
        d_pos.decompose()

    for d_entry in soup.find_all("d:entry"):
        if not isinstance(d_entry, Tag):
            continue
        d_entry.unwrap()


exclude_classes = {
    "phrases_block",
    "phrases_title",
    "phrasalverbs_block",
    "phrasalverbs_title",
    "origin_block",
    "origin_title",
    "derivatives_block",
    "derivatives_title",
    "usage_block",
    "usage_title",
    "note_block",
    "origin_inline",
}
attrs_to_remove = ["id", "linebreaks"]


def clean_attributes(soup: BeautifulSoup):
    """
    Remove specified attributes from all tags in the soup.
    If attrs_to_remove is None, remove 'id' and 'class' by default.
    """
    for tag in soup.find_all(True):
        if not isinstance(tag, Tag):
            continue
        # Handle 'class' attribute with exclude list
        if "class" in tag.attrs:
            kept_classes = [cls for cls in tag["class"] if cls in exclude_classes]
            if kept_classes:
                tag["class"] = cast(_AttributeValue, kept_classes)
            else:
                del tag["class"]

        # Remove other specified attributes
        for attr in attrs_to_remove:
            if attr in tag.attrs:
                del tag.attrs[attr]


def ensure_space_after_tags(soup: BeautifulSoup, tag_names):
    """
    Ensures there is a space after tags if the next sibling is a letter.
    """
    for tag_name in tag_names:
        for tag in soup.find_all(tag_name):
            next_sibling = tag.next_sibling
            if (
                isinstance(next_sibling, NavigableString)
                and next_sibling
                and not next_sibling.startswith(" ")
                and next_sibling[0].isalpha()
            ):
                # Insert a space at the start of the next sibling
                tag.insert_after(NavigableString(" " + next_sibling))
                next_sibling.extract()


def strip_title_whitespace(soup: BeautifulSoup):
    """
    Strips leading/trailing whitespace from the text of all *_title tags.
    """
    title_classes = [
        "usage_title",
        "origin_title",
        "derivatives_title",
        "phrases_title",
        "phrasalverbs_title",
    ]
    for cls in title_classes:
        for tag in soup.find_all(class_=cls):
            if not isinstance(tag, Tag):
                continue
            # Only strip if the tag contains a single NavigableString
            if len(tag.contents) == 1 and isinstance(tag.contents[0], NavigableString):
                original = tag.contents[0]
                stripped = original.strip()
                if stripped != original:
                    tag.contents[0].replace_with(NavigableString(stripped))
