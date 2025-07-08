"""Module to check if specified class (or class set) is present"""

from bs4 import BeautifulSoup
from bs4 import Tag

from .span_converters import (
    STYLE_MAP,
    APPLE_STYLE_MAP,
    COMPOSITE_STYLE_MAP,
)
from .process_main_definition import CLASS_SETS


def is_class(tag: Tag, class_name: str) -> bool:
    """Return True if the element has the specified class"""
    return tag.has_attr("class") and class_name in tag["class"]


def has_all_classes(tag: Tag, required_classes: set[str]) -> bool:
    """Return True if the element has all the required classes."""
    return (
        tag.name == "span"
        and tag.has_attr("class")
        and required_classes.issubset(set(tag["class"]))
    )


# Collect all classes used for manipulation
known_classes = set(STYLE_MAP.keys()) | set(APPLE_STYLE_MAP.keys())
for combo in COMPOSITE_STYLE_MAP:
    known_classes.update(combo)
for s in CLASS_SETS.values():
    known_classes.update(s)

excluded_classes = {
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
    "note",
    "la",  # latin language,
    "date",
    "df",  # definition
    "tg_df",
    "dg",  # related to "date" class
    "x_xoLblBlk",
    "etym",
    "t_derivatives",
    "t_phrasalVerbs",
    "t_phrases",
    "eg",  # example
    "frac",  # fraction
    "fg",  # phrase
    "ge",  # regional language (British English, American English, etc.)
    "reg",  # language register
    "hg",  # heading and IPA parent
    "x_xh0",
    "hw",  # headword
    "pr",  # pronunciation
    "prx",  # pronunciation
    "t_IPA",
    "ph",  # pronunciation
    "tg_ph",  # pronunciation
    "infg",  # inflected form
    "lbl",  # the colon after label
    "subEntryBlock",
    "tg_subEntryBlock",
    "subEntry",
    "posg",  # part of speech
    "pos",  # part of speech
    "tg_pos",
    "q",
    "tg_q",
    "gp",
    "sg",
    # "tg_sg", # empty span, ignore
    "x_blk",
    "se1",  # sense / meaning
    "x_xd0",
    "x_xdt",
    "tg_msDict",
    "sj",
    "tg_eg",  # period
    "tg_etym",
    "tx",
    "vg",
    "tg_vg",  # parenthesis
    "tg_fg",  # parenthesis
    "tg_infg",  # parenthesis
    "trans",  # translation
    "tg_gg",  # square bracket
    "tg_lg",  # comma
    "tg_reg",  # comma
    "tg_nu",  # slash (fraction)
    "tg_tr",  # quotation mark
    "tg_xrg",  # colon
    "x_xo0",
    "x_xo1",
    "x_xo2",
    "x_xo2sub",
    "x_xo3",
    "x_xoh",
    "xrlabelGroup",
    "xrlabel",
    "tg_xrlabel",
    "x_xot",  # it can be paired with etym
    "tg_xr",  # supscript
    "xrg",
    "xr",
}


def find_unknown_classes_in_file(
    file_path: str, known_classes_set: set[str], excluded_classes_set: set[str]
) -> dict[str, set[str]]:
    """
    Find classes present in a single HTML file but not in known_classes or excluded_classes.
    Returns a dict: {class_name: set of filenames}
    """
    class_to_files = {}
    with open(file_path, encoding="utf-8") as f:
        soup = BeautifulSoup(f, "lxml")
        for tag in soup.find_all(class_=True):
            if isinstance(tag, Tag):
                for cls in tag.get("class") or []:
                    # Ignore tags with empty or whitespace-only content
                    if not tag.text.strip():
                        continue
                    if cls not in known_classes_set and cls not in excluded_classes_set:
                        class_to_files.setdefault(cls, set()).add(file_path)
    return class_to_files
