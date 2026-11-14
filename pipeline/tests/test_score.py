import numpy as np

from pipeline import config, score
from pipeline.hls import WEEKS

NAN = np.nan


def classify(values, snow=None):
    v = np.array(values, dtype=float)
    s = np.zeros(len(v), dtype=bool) if snow is None else np.array(snow, dtype=bool)
    return "".join(score.classify(v, s)[0])


def test_clear_looks_are_bare_or_green():
    assert classify([0.1, 0.6, 0.24, 0.25]) == "BGBG"


def test_short_gap_is_filled_between_looks():
    # 0.1 to 0.5 over a 3-week gap crosses the 0.25 threshold part way.
    assert classify([0.1, NAN, NAN, NAN, 0.5]) == "BBGGG"


def test_long_gap_is_bridged_only_when_both_ends_agree():
    gap = [NAN] * 8
    assert classify([0.1] + gap + [0.15]) == "B" + "b" * 8 + "B"
    assert classify([0.6] + gap + [0.7]) == "G" + "g" * 8 + "G"
    assert classify([0.1] + gap + [0.7]) == "B" + "U" * 8 + "G"


def test_very_long_gap_stays_unknown():
    gap = [NAN] * (config.MAX_BRIDGE_WEEKS + 1)
    assert classify([0.1] + gap + [0.1]) == "B" + "U" * len(gap) + "B"


def test_snow_is_never_bare():
    snow = [False, True, True, False, False, False, False, False, False, False]
    out = classify([0.1, NAN, NAN, NAN, NAN, NAN, NAN, NAN, NAN, 0.1], snow)
    assert out == "BSSbbbbbbB"


def test_edges_without_a_look_stay_unknown():
    assert classify([NAN, NAN, 0.5, NAN]) == "UUGU"


def test_exposed_weeks_are_a_subset_of_bare_weeks():
    status = np.array([list("BBGGbbUS" + "G" * (WEEKS - 8))])
    heavy = np.zeros((1, WEEKS), dtype=bool)
    heavy[0, [0, 2, 4, 6, 7]] = True
    c = score.count(status, heavy)
    assert c["bare_seen"] == 2 and c["bare_likely"] == 2
    assert c["exposed_seen"] == 1 and c["exposed_likely"] == 1
    assert c["exposed"] <= c["bare"]


def test_cover_crop_fills_bare_weeks_after_the_lag():
    status = np.array([list("G" * 30 + "B" * 22), list("B" * 10 + "G" * 42)])
    plan = score.cover_crop_plan(status, [23, 23], {})
    flat = "".join(plan.reshape(-1))
    assert flat[30:33] == "BBB" and set(flat[33:62]) == {"C"}
    assert (plan == score.BARE).sum() < (status == score.BARE).sum()


def test_cover_crop_stops_when_winter_wheat_is_sown():
    status = np.array([list("G" * 30 + "B" * 22), list("B" * 10 + "G" * 42)])
    traits = {score.WINTER_WHEAT: {"plant_week": 38, "harvest_week": 31}}
    plan = score.cover_crop_plan(status, [23, score.WINTER_WHEAT], traits)
    flat = "".join(plan.reshape(-1))
    assert flat[33:38] == "CCCCC" and set(flat[38:62]) == {"B"}


def test_grade_rewards_fewer_bare_weeks():
    low = score.grade({"bare": 5, "exposed": 0}, 1.0, 3)
    high = score.grade({"bare": 30, "exposed": 3}, 0.0, 3)
    assert low[1] == "A" and high[1] == "F" and low[0] > high[0]


def test_variety_counts_crops_and_legume_bonus():
    traits = {51: {"nitrogen_fixing": True}}
    assert score.variety_score([24, 24, 61, 0], traits) == 0
    assert score.variety_score([24, 23, 51, 31], traits) == 1.0


def test_swap_year_prefers_latest_fallow():
    assert score.pick_swap_year([24, 61, 23, 61, 24]) == 3
    assert score.pick_swap_year([24, 23, 24, 51, 24]) == 4


def test_new_crop_is_a_legume_unless_the_field_has_one():
    traits = {51: {"nitrogen_fixing": True}}
    options = [24, 23, 51, 31]
    assert score.pick_new_crop([24, 23, 24], traits, options, 51) == 51
    assert score.pick_new_crop([24, 51, 61], traits, options, 51) == 51
    # Already has a legume and no fallow: add the most common crop it lacks.
    assert score.pick_new_crop([24, 51, 24], traits, options, 51) == 23
