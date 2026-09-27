from pypagekit.cli.exit_codes import EXECUTION_ERROR, SUCCESS, USAGE_ERROR


def test_cli_exit_codes_are_stable() -> None:
    assert SUCCESS == 0
    assert EXECUTION_ERROR == 1
    assert USAGE_ERROR == 2
