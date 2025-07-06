"""Module to process HTML files from Apple Dictionary."""

from bs4 import BeautifulSoup

from .span_converters import (
    convert_span_styles,
    convert_apple_span_styles,
)
from .wrapinbrackets import wrap_class_text_with_brackets
from .process_definition_phrases import (
    convert_x_xo_blocks,
    convert_subsenses_to_list,
)
from .process_main_definition import convert_senses_to_list
from .cleanup import (
    remove_bullet_spans,
    convert_origin_block,
    convert_derivatives_block,
    convert_usage_note_block,
    inject_hw_linebreaks,
    remove_empty_tags,
    convert_heading_spans_to_p,
)


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
    convert_usage_note_block(soup)
    inject_hw_linebreaks(soup)
    remove_empty_tags(soup)
    convert_heading_spans_to_p(soup)
    return str(soup.prettify())
