import pytest

from common import llm
from common.evidence import quote_found, unsupported_numbers
from common.util import BadAnswer, parse_json


def test_parse_json_tolerates_fences_and_prose():
    assert parse_json('Here you go:\n```json\n{"a": 1}\n```') == {"a": 1}
    assert parse_json("[1, 2]") == [1, 2]
    with pytest.raises(BadAnswer):
        parse_json("no json here")


def test_quote_found_ignores_case_punctuation_and_spacing():
    source = "The unit stopped cooling overnight.  It's already 86 inside!"
    assert quote_found("unit stopped COOLING overnight", source)
    assert quote_found("stopped cooling ... already 86 inside", source)
    assert not quote_found("the unit is fine", source)
    assert not quote_found("cooling", source)  # too short to count as evidence


def test_unsupported_numbers_catches_invented_figures():
    allowed = [48210.0, 12.5, 37]
    text = "Revenue was $48,210 in 2026, up 12.5%, across 37 jobs and 4 branches; margin hit 31%."
    assert unsupported_numbers(text, allowed) == ["31%"]


def test_from_env_explains_what_to_set():
    with pytest.raises(llm.ModelError, match="ANTHROPIC_API_KEY"):
        llm.from_env({})
    with pytest.raises(llm.ModelError, match="PLAYBOOK_MODEL"):
        llm.from_env({"PLAYBOOK_PROVIDER": "openai", "OPENAI_API_KEY": "k"})
    model = llm.from_env({"ANTHROPIC_API_KEY": "k"})
    assert model.name == llm.ANTHROPIC_DEFAULT


def test_parse_json_returns_a_list_when_the_list_comes_first():
    assert parse_json('[{"a": 1}, {"a": 2}]') == [{"a": 1}, {"a": 2}]
    assert parse_json('[{"a": 1}]') == [{"a": 1}]


def test_csv_cells_that_look_like_formulas_are_made_inert(tmp_path):
    from common.util import read_csv, write_csv

    rows = [{"a": '=HYPERLINK("http://x.example","click")', "b": "-12.50", "c": "@SUM(A1)", "d": 7, "e": "Cafe"}]
    path = write_csv(tmp_path / "x.csv", rows, ["a", "b", "c", "d", "e"])
    got = read_csv(path)[0]
    assert got["a"].startswith("'=") and got["c"].startswith("'@")
    assert got["b"] == "-12.50" and got["d"] == "7" and got["e"] == "Cafe"


def test_a_quote_matches_whole_words_only():
    from common.evidence import quote_found

    assert quote_found("the unit", "Is the unit on the roof?", min_words=1)
    assert not quote_found("unit", "Our community center needs a quote", min_words=1)


def test_a_value_must_appear_in_its_quote():
    from common.evidence import value_in_quote

    assert value_in_quote("RTU-2", "replace rtu 2 on the roof")
    assert value_in_quote("4417-631", "serial 4417631, a Carrier")
    assert not value_in_quote("4417-632", "serial 4417631, a Carrier")
    assert not value_in_quote("2", "unit 12 is down")
    assert not value_in_quote("", "anything")
