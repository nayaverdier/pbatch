def test_module_import():
    import pbatch

    pbatch.partition
    pbatch.pmap
    pbatch.postpone
    pbatch.PMapException
    pbatch.VERSION


def test_function_import():
    from pbatch import VERSION, PMapException, partition, pmap, postpone  # noqa: F401
