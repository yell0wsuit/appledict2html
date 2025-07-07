"""Module for post-processing the HTML"""

from bs4 import BeautifulSoup, Tag
from bs4.element import NavigableString


def cleanup_stuff(soup: BeautifulSoup):
    """Cleanup stuff"""
    remove_bullet_spans(soup)
    convert_origin_block(soup)
    convert_derivatives_block(soup)
    convert_usage_note_block(soup)
    inject_hw_linebreaks(soup)
    remove_empty_tags(soup)
    convert_heading_spans_to_p(soup)
    convert_phrasal_verbs_block(soup)
    convert_phrasal_block(soup)
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
        etym_div["class"] = ["origin_block"]  # type: ignore

        for child in etym_div.find_all("span", recursive=True):
            if not isinstance(child, Tag):
                continue

            child_classes = set(child.get("class") or [])

            if "x_xo1" in child_classes:
                child.name = "p"
                child.attrs.clear()

            elif {"gp", "x_xoLblBlk", "ty_label", "tg_etym"}.issubset(child_classes):
                child.name = "p"
                child["class"] = ["origin_title"]  # type: ignore


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
        div["class"] = ["derivatives_block"]  # type: ignore

        for span in div.find_all("span", recursive=True):
            if not isinstance(span, Tag):
                continue

            classes = set(span.get("class") or [])

            if {"gp", "x_xoLblBlk", "ty_label", "tg_subEntryBlock"}.issubset(classes):
                span.name = "p"
                span["class"] = ["derivatives_title"]  # type: ignore

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
        note_div["class"] = ["usage_block"]  # type: ignore

        for span in note_div.find_all("span", recursive=True):
            if not isinstance(span, Tag):
                continue

            classes = set(span.get("class") or [])

            if {"lbl", "x_blk"}.issubset(classes):
                span.name = "p"
                span["class"] = ["usage_title"]  # type: ignore


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
        div["class"] = ["phrasalverbs_block"]  # type: ignore

        for span in div.find_all("span", recursive=True):
            if not isinstance(span, Tag):
                continue

            classes = set(span.get("class") or [])

            if {"gp", "x_xoLblBlk", "ty_label", "tg_subEntryBlock"}.issubset(classes):
                span.name = "p"
                span["class"] = ["phrasalverbs_title"]  # type: ignore


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
        div["class"] = ["phrases_block"]  # type: ignore

        for span in div.find_all("span", recursive=True):
            if not isinstance(span, Tag):
                continue

            classes = set(span.get("class") or [])

            if {"gp", "x_xoLblBlk", "ty_label", "tg_subEntryBlock"}.issubset(classes):
                span.name = "p"
                span["class"] = ["phrases_title"]  # type: ignore


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
                tag["class"] = kept_classes  # type: ignore
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
