import os


def test_py(setup_docs_test):
    import pattern_general  # noqa: F401

    assert os.path.isfile(os.path.join('..', '_images', 'pattern_general.png'))
