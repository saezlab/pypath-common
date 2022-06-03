# Configuration file for the Sphinx documentation builder.

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
from pathlib import Path
from datetime import datetime
import sys

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent.parent))

import pypath_common  # noqa: E402

# -- Project information

project = "pypath_common"
version = pypath_common.__version__
release = f"master ({version})"
author = pypath_common.__author__
copyright = f"{datetime.now():%Y}, OmniPath developers"


# -- General configuration

extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_autodoc_typehints",
    "sphinx.ext.intersphinx",
    "sphinx.ext.autosummary",
    "sphinx_last_updated_by_git",
    "sphinx.ext.autosectionlabel",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
}
intersphinx_disabled_domains = ["std"]

templates_path = ["_templates"]

# -- Options for HTML output
master_doc = "index"

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_theme_options = {
    "navigation_depth": 4,
    "logo_only": True,
    "display_version": True,
}
html_context = {
    "display_github": True,  # Integrate GitHub
    "github_user": "saezlab",  # Username
    "github_repo": "pypath-cache",  # Repo name
    "github_version": "master",  # Version
    "conf_py_path": "/docs/source/",  # Path in the checkout to the docs root
}
html_show_sphinx = False

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
autosummary_generate = True
autodoc_member_order = "alphabetical"
autodoc_typehints = "signature"
autodoc_docstring_signature = True
autodoc_follow_wrapped = False
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_use_rtype = True
napoleon_use_param = True
napoleon_custom_sections = [("Params", "Parameters")]
todo_include_todos = False

# -- Options for EPUB output
epub_show_urls = "footnote"
