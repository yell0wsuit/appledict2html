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
from .cleanup import cleanup_stuff


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
    cleanup_stuff(soup)
    return "<!DOCTYPE html>\n" + str(soup)
