# Changelog

## [1.1.0] - 2025-07-07

### Added

- Add space after some specific tags.
- Update HTML output to include DOCTYPE declaration.
- Add `clean_attributes` to remove unwanted tag attributes.
- Add new cleanup helpers for phrasal verbs, phrases, and unwrapping tags.

### Changed

- Refactor blocks to use `<section>` and clean up titles.
- Convert 'gg' spans inside 'eg' as `<code>` tags.
- Refactor HTML cleanup into single function.
- Improve whitespace handling in `wrap_class_text_with_brackets`.
- Fix Python lint errors.
