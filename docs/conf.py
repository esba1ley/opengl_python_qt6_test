"""Sphinx configuration for the local HTML documentation.

Build with ``make html`` in this directory. The program's own modules are
imported by autodoc, so the build needs the same environment that runs the
program, plus the packages in ``requirements.txt``.
"""
import sys
from pathlib import Path

# Modules live directly in src/ and import each other by name.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import main  # noqa: E402

project = "Qt6 OpenGL Test"
author = "Erik S. Bailey"
release = main.__version__
version = release

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "myst_parser",
    "sphinxcontrib.plantuml",
]

# Diagrams under docs/diagrams/ are rendered at build time. PlantUML needs a
# Java runtime; "plantuml" here is the MacPorts launcher on PATH. The class
# and call-graph diagrams go through Graphviz, and PlantUML rejects the SVG
# from conda-forge's Graphviz 13, so prefer the MacPorts dot when present.
_macports_dot = Path("/opt/local/bin/dot")
plantuml = "plantuml" + (f" -graphvizdot {_macports_dot}" if _macports_dot.exists() else "")
plantuml_output_format = "svg_img"

# The prose pages are the repository's Markdown READMEs, pulled in with
# MyST's include directive so they stay the single source.
source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
myst_heading_anchors = 3

napoleon_google_docstring = False
napoleon_numpy_docstring = True

autodoc_member_order = "bysource"
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_static_path = []
