"""Profiles 测试共享夹具（pytest fixture 自动发现）。"""

import os
import tempfile

import pytest


@pytest.fixture
def temp_profiles(monkeypatch):
    """用临时文件覆盖配置路径。"""
    tmp = tempfile.mkdtemp()
    pf = os.path.join(tmp, "profiles.json")
    monkeypatch.setattr("winrandr.profiles._PROFILES_FILE", pf)
    return pf
