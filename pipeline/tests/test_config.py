from pipeline import config


def test_grade_weights_sum_to_100():
    assert sum(config.GRADE_WEIGHTS.values()) == 100


def test_grade_cutoffs_descend():
    cutoffs = [config.GRADE_CUTOFFS[g] for g in "ABCD"]
    assert cutoffs == sorted(cutoffs, reverse=True)
