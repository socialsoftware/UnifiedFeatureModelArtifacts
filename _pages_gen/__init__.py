"""Generates the GitHub Pages appendix from the ``artifacts/`` directory.

Invoked through the ``generate.py`` shim at the repository root, never directly:
the generated pages carry a banner naming that script, and ``_config.yml``
excludes it by name.

The package is laid out bottom-up, each layer importing only from the ones
below it:

    paths       repository locations and BuildError
    config      the tables that vary when a tool, paper or skill is added
    util        small pure helpers
    artifacts   logical key -> real file registry, and the one built artifact
    parse       the artifact file formats, read into plain Python data
    render      stateless HTML/Markdown fragments, and the page writer
    pages/      one module per section of the site
    report      the colour-count cross-check
    postprocess prune generated pages, then resolve {{BASE}}
    cli         orchestration

The leading underscore in the directory name is load-bearing: the Pages source
is the repository root, and Jekyll skips entries whose name starts with ``_``
before it consults ``exclude:``. Without it this source would be published as
site content.
"""
