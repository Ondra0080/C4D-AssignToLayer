# Changelog

## v1.2.2
- Split into two standalone language plugins (CS / EN)
- Fixed language handling (no runtime detection)
- Unified icon handling
- Improved dialog clarity
- Stable behavior in Cinema 4D 2024+

## v1.2.0
- Runtime language detection (CZ / EN / DE)
- Initial public version

## [1.5.1] - 2026-05-24

### Fixed
- Fixed the layer list width in the custom layer selector.
- Removed unwanted horizontal scrolling in the existing layers list.
- Adjusted the internal row width so selected layer rows match the visible list area more consistently.
- Improved compact dialog layout for Cinema 4D 2024.x.

### Notes
- This is a small UI bugfix release based on v1.5.0.
- No functional changes were made to the layer assignment logic.

---

## [1.5.0] - 2026-05-24

### Added
- First unified official release of **AssignToLayer**.
- Added official Maxon Plugin ID: `1068663`.
- Added automatic UI language detection based on the active Cinema 4D language.
  - Czech Cinema 4D UI → Czech plugin UI.
  - English Cinema 4D UI → English plugin UI.
  - Any other Cinema 4D language → English fallback.
- Added support for both Czech and English UI strings in a single plugin build.
- Added persistent settings:
  - remembers the last selected target layer,
  - remembers the overwrite existing layer option.
- Added custom layer list with visible layer color swatches.
- Added compact dialog layout.

### Changed
- Merged the previous separate `AssignToLayer_CS` and `AssignToLayer_EN` builds into one unified plugin.
- Replaced temporary development Plugin IDs with the official Plugin ID `1068663`.
- Plugin folder is now simply named:

```text
AssignToLayer
