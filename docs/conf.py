# Configuration file for the Sphinx documentation builder
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

import importlib.metadata
import os
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, os.path.abspath(".."))


# -- Project information -----------------------------------------------------


with Path("../pyproject.toml").open("rb") as f:
    pkg_info = tomllib.load(f)
project = pkg_info["project"]["name"]
author = "SalishSeaCast Project Contributors and The University of British Columbia"
pkg_creation_year = 2013
copyright = f"{pkg_creation_year} – present, {author}"

# The short X.Y version
version = importlib.metadata.version(project)
# The full version, including alpha/beta/rc tags
release = version


# -- General configuration ------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "notfound.extension",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
]

# Intersphinx configuration
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "salishseadocs": ("https://salishsea-meopar-docs.readthedocs.io/en/latest/", None),
    "nemocmd": ("https://nemo-cmd.readthedocs.io/en/latest/", None),
}

todo_include_todos = True

autodoc_mock_imports = [
    "arrow",
    "cliff",
    "cliff.command",
    "cliff.commandmanager",
    "hglib",
    "nemo_cmd",
    "nemo_cmd.api",
    "nemo_cmd.prepare",
    "nemo_cmd.utils",
    "yaml",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix(es) of source filenames.
# You can specify multiple suffixes as a list of strings:
source_suffix = {".rst": "restructuredtext"}

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "sphinx_rtd_theme"

# A shorter title for the navigation bar.  Default is the same as html_title.
html_short_title = "SalishSeaCmd"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
html_favicon = "_static/MEOPAR_favicon.ico"

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
html_last_updated_fmt = "%b %d, %Y"

# If false, no module index is generated.
html_domain_indices = True

# If false, no index is generated.
html_use_index = True

# If true, the index is split into individual pages for each letter.
html_split_index = False

# If true, links to the reST sources are added to the pages.
html_show_sourcelink = True

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
html_show_sphinx = True

# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
html_show_copyright = True
