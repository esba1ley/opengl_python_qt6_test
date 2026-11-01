# Journal

Newest first.

## 2026-11-01 — Stop shadowed faces catching light

- Confirmed the light is directional, so all rays are parallel and the cube
  cannot cast shadows on itself except by face orientation.
- Added a geometric-normal gate to `CUBE_FRAGMENT_BODY` in `src/shaders.py`.
  See the matching entry in `DECISIONS.md`.
- Verified with before/after frames lit from behind the visible faces, plus
  `--check` passing. Default view is visually unchanged.

**Next:** Nothing queued.

## 2026-11-01 — First run on macOS

- Ran `python3 src/main.py --check` on an Apple M4 Mac from the `esb312`
  conda environment. It failed with `version '140' is not supported` because
  macOS handed out an OpenGL 2.1 context.
- Added a macOS-only 3.2 core profile request in `src/main.py` and changed
  `src/widget.py` to extend the default format rather than replace it. See
  the 2026-11-01 entry in `DECISIONS.md`.
- Self-test passes all six checks; a saved frame shows the cube, grid, axes
  and light dot correctly. Axes are one pixel wide on macOS.
- Documented the macOS requirement in `README.md` and `.claude/CLAUDE.md`, and
  created `ARCHITECTURE.md`, `DECISIONS.md` and this journal.

**Next:** Nothing queued. The Pi path should be re-run to confirm the
`defaultFormat()` change is neutral there.
