from wordlette.utils.unbounded_range import Range


def test_unbounded_upper_bound():
    r = Range(start=0)
    assert 0 in r
    assert 10**1000 in r
    assert -1 not in r


def test_unbounded_lower_bound():
    r = Range(end=0)
    assert 0 in r
    assert -(10**1000) in r
    assert 1 not in r


def test_unbounded_both_bounds():
    r = Range()
    assert 0 in r
    assert 10**1000 in r
    assert -(10**1000) in r


def test_bounded():
    r = Range(start=0, end=10)
    assert 0 in r
    assert 10 in r
    assert 5 in r
    assert 11 not in r
    assert -1 not in r
    assert 100 not in r


def test_negative_step_unbounded_upper_bound():
    r = Range(start=0, step=-1)
    assert 0 in r
    assert -(10**1000) in r
    assert 1 not in r


def test_negative_step_unbounded_lower_bound():
    r = Range(end=0, step=-1)
    assert 0 in r
    assert 10**1000 in r
    assert -1 not in r


def test_negative_step_unbounded_both_bounds():
    r = Range(step=-1)
    assert 0 in r
    assert 10**1000 in r
    assert -(10**1000) in r


def test_negative_step_bounded():
    r = Range(start=10, end=0, step=-1)
    assert 0 in r
    assert 10 in r
    assert 5 in r
    assert 11 not in r
    assert -1 not in r
    assert 100 not in r


def test_large_step_unbounded_upper_bound():
    r = Range(start=0, step=10)
    assert 0 in r
    assert 10**1000 in r
    assert 1 not in r


def test_large_step_unbounded_lower_bound():
    r = Range(end=0, step=10)
    assert 0 in r
    assert -(10**1000) in r
    assert -1 not in r
