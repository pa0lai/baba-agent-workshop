from workshop.tasks import ALL_SUITE, FINAL_SUITE, PUBLIC_SUITE, SUITES


def test_all_suite_contains_ten_unique_levels():
    assert len(PUBLIC_SUITE) == 3
    assert len(FINAL_SUITE) == 7
    assert len(ALL_SUITE) == 10
    assert len({item["task"] for item in ALL_SUITE}) == 10
    assert len({item["seed"] for item in ALL_SUITE}) == 10


def test_challenge_ends_with_compositional_levels():
    assert FINAL_SUITE[-2]["task"] == "env/two_room-make_you-make_win"
    assert FINAL_SUITE[-1]["task"] == "env/two_room-make_wall_win"
    assert SUITES["all"] == ALL_SUITE
