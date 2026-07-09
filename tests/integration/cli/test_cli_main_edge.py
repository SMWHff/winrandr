"""CLI 入口集成测试——set 操作调用验证与边缘场景。"""

from unittest.mock import patch

import pytest

from tests.conftest import _fake_display
from winrandr.cli import main as cli_main


def test_main_set_resolution_called():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli.handlers.set_resolution", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "-m", "1920x1080"]):
                cli_main()
            assert mock_fn.called is True


def test_main_set_position_called():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli.handlers.set_position", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "-p", "1920x0"]):
                cli_main()
            assert mock_fn.called is True


def test_main_set_primary_called():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli.handlers.set_primary", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "--primary"]):
                cli_main()
            assert mock_fn.called is True


def test_main_set_off_called():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli.handlers.set_off", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "--off"]):
                cli_main()
            assert mock_fn.called is True


def test_main_set_brightness_called():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli.handlers.set_brightness", return_value=True) as mock_fn:
            with patch("sys.argv", ["winrandr", "-o", "DISPLAY1", "--brightness", "0.8"]):
                cli_main()
            assert mock_fn.called is True


def test_main_query_prop_json():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli.get_display_props", return_value={"device_id": "TEST"}):
            with patch("sys.argv", ["winrandr", "--prop", "--json"]):
                cli_main()


def test_main_listmonitors_json():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("sys.argv", ["winrandr", "--listmonitors", "--json"]):
            cli_main()


def test_main_listmodes_no_displays():
    with patch("winrandr.cli.handlers.list_displays", return_value=[]):
        with patch("sys.argv", ["winrandr", "--listmodes"]):
            cli_main()


def test_main_noprimary_failure():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with patch("winrandr.cli.set_noprimary", return_value=False):
            with patch("sys.argv", ["winrandr", "--noprimary"]):
                with pytest.raises(SystemExit):
                    cli_main()


def test_main_query_output_not_found():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display("DISPLAY1")]):
        with patch("winrandr.cli.list_providers", return_value=[]):
            with pytest.raises(SystemExit):
                with patch("sys.argv", ["winrandr", "--output", "DISPLAY99"]):
                    cli_main()


def test_main_missing_output_for_modop():
    with patch("winrandr.cli.list_displays", return_value=[_fake_display()]):
        with pytest.raises(SystemExit):
            with patch("sys.argv", ["winrandr", "--mode", "1920x1080"]):
                cli_main()
