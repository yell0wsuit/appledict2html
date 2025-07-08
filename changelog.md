# Changelog

## [1.2.1] - 2025-07-08

### v1.2.1 fixes

- `process_folder` now correctly excludes files ending with `-htmlprocessed.html` instead of `_processed.html`, which could match unintended filenames. While v1.1.2 attempted to fix this, the issue was not fully resolved.

## [1.2.0] - 2025-07-08

### v1.2.0 additions

- Add `--sanity-check` to check for unknown/undocumented classes in the HTML file. This is to help with debugging and development.
- Convert `<span class="etym x_xo3">` (ORIGIN in the PHRASES section) to `<p>` and remove its classes.

### v1.2.0 changes

- Refactored `convert_xo1_to_list` in `process_definition_phrases.py` to better preserve and structure children, including inline origin blocks, when converting `x_xo1` and `x_xo2` spans.

## [1.1.2] - 2025-07-07

### v1.1.2 fixes

- Change output file name to include `-htmlprocessed` suffix. This is to avoid confusion with the original file.

## [1.1.1] - 2025-07-07

### v1.1.1 changes

- Remove success print statements for `--multiple` mode to reduce console noise.
- Add logging to `io_utils.py` to log errors to `appledict2semantic.log`.

## [1.1.0] - 2025-07-07

### v1.1.0 additions

- Add space after some specific tags.
- Update HTML output to include DOCTYPE declaration.
- Add `clean_attributes` to remove unwanted tag attributes.
- Add new cleanup helpers for phrasal verbs, phrases, and unwrapping tags.

### v1.1.0 changes

- Refactor blocks to use `<section>` and clean up titles.
- Convert 'gg' spans inside 'eg' as `<code>` tags.
- Refactor HTML cleanup into single function.
- Improve whitespace handling in `wrap_class_text_with_brackets`.
- Fix Python lint errors.
