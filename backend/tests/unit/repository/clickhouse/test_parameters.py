from app.repository.clickhouse.client import parameter


def test_array_parameters_use_clickhouse_literals_without_changing_scalar_values() -> None:
    assert parameter([1, 9007199254740993]) == "[1,9007199254740993]"
    assert parameter(["O'Brien", "a\\b"]) == "['O\\'Brien','a\\\\b']"
    assert parameter(["line\n"]) == "['line\\n']"
    assert parameter("%' OR 1=1") == "%' OR 1=1"
    assert parameter([]) == "[]"
