from src.slugs import slugify


def test_converts_simple_label():
    assert slugify("Release Notes") == "release-notes"


def test_trims_outer_spaces():
    assert slugify("  Docs  ") == "docs"
