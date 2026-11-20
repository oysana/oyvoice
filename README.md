# OyVoice

Public storefront for OyVoice — a dictation bridge for Pop!_OS 24.04 COSMIC.

Site: https://oysana.github.io/oyvoice/

Sales are not open yet; this repository currently hosts only the static
landing (EN + RU). Contact: GitHub Issues.

## Post-hero design

Both locale pages use the same stylesheet and asset set. Keep the section
order and check both locales with `python3 scripts/check-design.py`.
The workflow runs this check on pull requests.

| Role | Use |
| --- | --- |
| `bento` | Explain one process with one large visual and at least two related tiles. |
| `editorial` | Keep compatibility and release constraints visible in labeled rows. |
| `action` | State availability and show one real action. |
| `faq` | Use native details and summary for optional answers. |

Define spacing, color, shape, and interaction values once in `.oy-story`.
Use native links and headings inside sections. The light-wave illustration
has two WebP sizes. The diagrams are inline-independent SVG files. The
availability panel draws its shader on entry and resize. Its CSS background
works without WebGL or JavaScript.

Use Kargul's spacing, grid, and image hierarchy for OyVoice. Keep the
storefront's own typography and pixel controls. `--font-display` pairs
Geist Pixel Square with Geist Mono for Cyrillic. `--font-body` uses Inter
for explanatory copy. Both roles load their fonts from `assets/fonts/`.

The [Geist v1.9.2](https://github.com/vercel/geist-font/tree/v1.9.2)
webfonts and the Latin/Cyrillic subset of
[Inter v4.1](https://github.com/rsms/inter/tree/v4.1) ship with their
SIL Open Font License files.
