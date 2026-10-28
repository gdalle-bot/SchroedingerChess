"""Sphinx configuration."""

project = "SchroedingerChess"
author = "Guillaume Dalle"
copyright = "2018-2026, Guillaume Dalle"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
]

autodoc_member_order = "bysource"
autodoc_default_options = {"members": True, "show-inheritance": True}

html_theme = "furo"
html_title = "Schrödinger Chess"
exclude_patterns = ["_build"]
