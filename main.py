"""
Convert Apple Dictionary HTML spans into semantic, readable HTML.
This removes the dependency on CSS styles by converting span class names into
appropriate semantic HTML tags and structural markup.
"""

import os
from bs4 import BeautifulSoup

from appledict2html.helpers.span_converters import (
    convert_span_styles,
    convert_apple_span_styles,
)
from appledict2html.helpers.wrapinbrackets import wrap_class_text_with_brackets
from appledict2html.helpers.process_definition_phrases import (
    convert_x_xo_blocks,
    convert_subsenses_to_list,
)
from appledict2html.helpers.process_main_definition import convert_senses_to_list
from appledict2html.helpers.cleanup import (
    remove_bullet_spans,
    convert_origin_block,
    convert_derivatives_block,
    convert_usage_note_block,
    inject_hw_linebreaks,
    remove_empty_tags,
    convert_heading_spans_to_p,
)


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
    convert_usage_note_block(soup)
    inject_hw_linebreaks(soup)
    remove_empty_tags(soup)
    convert_heading_spans_to_p(soup)
    return str(soup.prettify())


INPUT_FILENAME = "43957_handle.html"
INPUT_FILENAME = "03183_anathematize.html"

with open(INPUT_FILENAME, "r", encoding="utf-8") as f:
    html = f.read()

HTML_OUT = process_html(html)

# Append _processed before the .html extension
base, ext = os.path.splitext(INPUT_FILENAME)
OUTPUT_FILENAME = f"{base}_processed{ext}"

with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
    f.write(HTML_OUT)
