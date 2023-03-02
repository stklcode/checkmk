#!/usr/bin/env python3
# Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

import pytest

from tests.testlib import CMKWebSession
from tests.testlib.site import Site

from cmk.utils import version as cmk_version


def test_www_dir(site: Site) -> None:
    web = CMKWebSession(site)

    # unauthenticated = denied
    web.get("/%s/testfile" % site.id, expected_code=401)

    try:
        site.write_text_file("var/www/testfile.html", "123")
        assert web.get("/%s/testfile.html" % site.id, auth=("cmkadmin", "cmk")).text == "123"
    finally:
        site.delete_file("var/www/testfile.html")


def test_base_path_redirects(site: Site) -> None:
    web = CMKWebSession(site)
    expected_target = "%s://%s:%d/%s/check_mk/" % (
        site.http_proto,
        site.http_address,
        site.apache_port,
        site.id,
    )

    web.check_redirect("/%s" % site.id, expected_target=expected_target)
    web.check_redirect("/%s/" % site.id, expected_target=expected_target)
    web.check_redirect("/%s/check_mk" % site.id, expected_target=expected_target)


def test_base_path_access(site: Site) -> None:
    web = CMKWebSession(site)
    expected_target = "/%s/check_mk/login.py?_origtarget=index.py" % site.id

    # TODO: Figure out if which status code we *really* expect here: 301 or 302?
    web.check_redirect("/%s/check_mk/" % site.id, expected_target=expected_target)

    web.check_redirect("/%s/check_mk/index.py" % site.id, expected_target=expected_target)


def test_cmk_agents_access(site: Site) -> None:
    web = CMKWebSession(site)
    body = web.get("/%s/check_mk/agents" % site.id).text
    assert "Index of" in body


def test_cmk_local_agents_access(site: Site) -> None:
    web = CMKWebSession(site)
    body = web.get("/%s/check_mk/local/agents" % site.id).text
    assert "Index of" in body


def test_cmk_sounds(site: Site) -> None:
    web = CMKWebSession(site)
    response = web.get("/%s/check_mk/sounds/ok.wav" % site.id)
    assert response.headers["Content-Type"] == "audio/x-wav"


def test_cmk_automation(site: Site) -> None:
    web = CMKWebSession(site)
    response = web.get("/%s/check_mk/automation.py" % site.id)
    assert response.text == "Missing secret for automation command."


@pytest.mark.skipif(cmk_version.is_raw_edition(), reason="agent deployment not supported on CRE")
def test_cmk_deploy_agent(site: Site) -> None:
    web = CMKWebSession(site)
    response = web.get("/%s/check_mk/deploy_agent.py" % site.id)
    assert response.text.startswith("ERROR: Missing")


def test_cmk_run_cron(site: Site) -> None:
    web = CMKWebSession(site)
    web.get("/%s/check_mk/run_cron.py" % site.id)


def test_cmk_pnp_template_removed(site: Site) -> None:
    web = CMKWebSession(site)
    web.get("/%s/check_mk/pnp_template.py" % site.id, expected_code=404)


def test_cmk_ajax_graph_images(site: Site) -> None:
    web = CMKWebSession(site)
    response = web.get("/%s/check_mk/ajax_graph_images.py" % site.id)
    assert response.text == ""


def test_trace_disabled(site: Site) -> None:
    web = CMKWebSession(site)
    # TRACE is disabled by using "TraceEnable Off" in apache config
    web.request("TRACE", "/", expected_code=405)


def test_track_disabled(site: Site) -> None:
    web = CMKWebSession(site)
    # all methods but GET, POST, HEAD are disabled in the apache config.
    web.request("TRACK", "/", expected_code=405)


def test_options_disabled(site: Site) -> None:
    web = CMKWebSession(site)
    # all methods but GET, POST, HEAD are disabled in the apache config.
    web.request("OPTIONS", "/", expected_code=405)


def test_content_security_policy_header(site: Site) -> None:
    """The CSP can now be manipulated by the wsgi app. therefore and thanks to
    https://bz.apache.org/bugzilla/show_bug.cgi?id=62380 to set the CSP is now
    a bit more difficult.

    for once there are two header tables, one for the success case and one for
    "always". But they are not merged... So we only set the always header if
    the status-code is not 200. Since this is a big mess, here are some tests
    so hopefully we catch errors early on.

    The only page that uses the custom CSP is the SAML SSO page. But to access
    it we need a IDP set up which is currently not feasible in a int-test."""
    web = CMKWebSession(site)

    # This is a copy of omd/packages/apache-omd/skel/etc/apache/conf.d/security.conf
    default_csp = (
        "default-src 'self' 'unsafe-inline' 'unsafe-eval' ssh: rdp:; "
        "img-src 'self' data: https://*.tile.openstreetmap.org/ ; "
        "connect-src 'self' https://crash.checkmk.com/ https://license.checkmk.com/api/verify "
        "https://license.checkmk.com/api/verification-result; "
        "frame-ancestors 'self' ; "
        "base-uri 'self'; "
        "form-action 'self' javascript: 'unsafe-inline'; "
        "object-src 'self'; "
        "worker-src 'self' blob:"
    )

    # No CSP for media files
    response = web.get("/%s/check_mk/sounds/ok.wav" % site.id)
    assert response.headers["Content-Type"] == "audio/x-wav"
    assert response.headers.get("Content-Security-Policy") is None

    # CSP for error pages
    response = web.request("OPTIONS", "/", expected_code=405)
    assert response.headers["Content-Security-Policy"] == default_csp

    # CSP for successful pages
    response = web.get("/%s/check_mk/login.py?_origtarget=index.py" % site.id)
    assert response.headers["Content-Security-Policy"] == default_csp
