# Changelog

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
