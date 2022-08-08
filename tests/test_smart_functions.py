from wordlette.smart_functions import call


def test_calling_with_optional_params():
    def test_func(test_arg):
        return test_arg

    assert call(test_func, test_arg="VALUE") == "VALUE"


def test_calling_with_default_params():
    def test_func(test_arg="NOVALUE"):
        return test_arg

    assert call(test_func, test_arg="VALUE") == "VALUE"
