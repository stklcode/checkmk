#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

import pytest  # type: ignore[import]

from testlib.base import Scenario

from cmk.utils.type_defs import Result

from cmk.base.data_sources import Mode
from cmk.base.data_sources.agent import AgentHostSections
from cmk.base.data_sources.piggyback import PiggybackConfigurator


@pytest.fixture(name="mode", params=(mode for mode in Mode if mode is not Mode.NONE))
def mode_fixture(request):
    return request.param


@pytest.mark.parametrize("ipaddress", [None, "127.0.0.1"])
def test_attribute_defaults(monkeypatch, ipaddress, mode):
    hostname = "testhost"
    Scenario().add_host(hostname).apply(monkeypatch)

    configurator = PiggybackConfigurator(hostname, ipaddress, mode=mode)
    assert configurator.hostname == hostname
    assert configurator.ipaddress == ipaddress
    assert configurator.mode is mode
    assert configurator.description.startswith("Process piggyback data from")
    assert configurator.summarize(Result.OK(AgentHostSections())) == (0, "", [])
    assert configurator.id == "piggyback"
