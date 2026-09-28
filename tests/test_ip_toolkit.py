"""Tests for the pure address-math functions in ip-toolkit.py.

The GUI is not exercised here -- every function under test returns a dict and
touches no widgets. The module filename has a hyphen, so it cannot be imported
with a plain `import`; it is loaded by path instead.
"""

import ipaddress
import importlib.util
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parent.parent / "ip-toolkit.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("ip_toolkit", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ipt = _load_module()


# ---- IPv6 Calculator -------------------------------------------------------
def test_calculate_ipv6_basic():
    r = ipt.calculate_ipv6("2001:db8::/32")
    assert r["network"] == "2001:db8::"
    assert r["first"] == "2001:db8::"
    assert r["last"] == "2001:db8:ffff:ffff:ffff:ffff:ffff:ffff"
    assert r["prefixlen"] == 32
    assert r["num_addresses"] == 2 ** 96


def test_calculate_ipv6_host_bits_are_masked_off():
    # strict=False, so a host address with a prefix gives its containing network.
    assert ipt.calculate_ipv6("2001:db8::1234/64")["network"] == "2001:db8::"


def test_calculate_ipv6_exploded_and_compressed_forms():
    r = ipt.calculate_ipv6("2001:db8::/64")
    assert r["compressed"] == "2001:db8::/64"
    assert r["exploded"] == "2001:0db8:0000:0000:0000:0000:0000:0000/64"


@pytest.mark.parametrize("text, fragment", [
    ("", "Enter an IPv6 address"),
    ("2001:db8::", "Missing prefix"),
    ("192.168.1.0/24", "IPv4 address"),
    ("not-an-address/64", "Invalid IPv6 network"),
])
def test_calculate_ipv6_errors(text, fragment):
    assert fragment in ipt.calculate_ipv6(text)["error"]


# ---- IPv4 Calculator -------------------------------------------------------
def test_calculate_ipv4_slash24():
    r = ipt.calculate_ipv4("192.168.1.0/24")
    assert r["network"] == "192.168.1.0"
    assert r["broadcast"] == "192.168.1.255"
    assert r["netmask"] == "255.255.255.0"
    assert r["wildcard"] == "0.0.0.255"
    assert (r["total"], r["usable"]) == (256, 254)
    assert (r["first_host"], r["last_host"]) == ("192.168.1.1", "192.168.1.254")


def test_calculate_ipv4_slash31_counts_both_addresses():
    # RFC 3021 point-to-point: no network/broadcast to subtract.
    r = ipt.calculate_ipv4("10.0.0.0/31")
    assert (r["total"], r["usable"]) == (2, 2)
    assert (r["first_host"], r["last_host"]) == ("10.0.0.0", "10.0.0.1")


def test_calculate_ipv4_slash32_is_a_single_host():
    r = ipt.calculate_ipv4("10.0.0.5/32")
    assert (r["total"], r["usable"]) == (1, 1)
    assert (r["first_host"], r["last_host"]) == ("10.0.0.5", "10.0.0.5")


@pytest.mark.parametrize("text, fragment", [
    ("", "Enter an IPv4 address"),
    ("192.168.1.1", "Missing prefix"),
    ("2001:db8::/32", "IPv6 address"),
    ("999.1.1.1/24", "Invalid IPv4 network"),
])
def test_calculate_ipv4_errors(text, fragment):
    assert fragment in ipt.calculate_ipv4(text)["error"]


# ---- Random Address Generator ---------------------------------------------
def test_random_host_stays_inside_the_given_prefix():
    net = ipaddress.ip_network("2001:db8:abcd::/48")
    for _ in range(50):
        r = ipt.random_address("Host in prefix", "2001:db8:abcd::/48")
        assert ipaddress.IPv6Address(r["address"]) in net


def test_random_blank_prefix_falls_back_to_global_unicast():
    r = ipt.random_address("Host in prefix", "  ")
    assert ipaddress.IPv6Address(r["address"]) in ipaddress.ip_network("2000::/4")
    assert "global unicast" in r["scope"]


@pytest.mark.parametrize("kind, cidr", [
    ("Documentation", "2001:db8::/32"),
    ("ULA", "fd00::/8"),
])
def test_random_fixed_ranges(kind, cidr):
    for _ in range(20):
        r = ipt.random_address(kind, "")
        assert ipaddress.IPv6Address(r["address"]) in ipaddress.ip_network(cidr)


@pytest.mark.parametrize("kind, prefix, fragment", [
    ("Host in prefix", "2001:db8::", "network with prefix"),
    ("Host in prefix", "192.168.1.0/24", "Enter an IPv6 network"),
    ("Nonsense", "", "Unknown generator type"),
])
def test_random_errors(kind, prefix, fragment):
    assert fragment in ipt.random_address(kind, prefix)["error"]


# ---- Prefix Converter ------------------------------------------------------
@pytest.mark.parametrize("text, count, subnets64", [
    ("0", 2 ** 128, 2 ** 64),
    ("48", 2 ** 80, 2 ** 16),
    ("64", 1, 1),
    ("128", 1, None),
])
def test_convert_prefix_length(text, count, subnets64):
    r = ipt.convert_prefix_length(text)
    assert r["count"] == (2 ** (128 - int(text)))
    assert r["subnets64"] == subnets64


def test_convert_prefix_length_accepts_leading_slash():
    assert ipt.convert_prefix_length("/64")["prefix"] == 64


def test_convert_prefix_length_mask():
    assert ipt.convert_prefix_length("64")["mask"] == (
        "ffff:ffff:ffff:ffff:0000:0000:0000:0000")


@pytest.mark.parametrize("text", ["", "abc", "129", "-1", "64.5"])
def test_convert_prefix_length_errors(text):
    assert "error" in ipt.convert_prefix_length(text)


def test_convert_address_form_round_trip():
    r = ipt.convert_address_form("2001:0db8:0000:0000:0000:0000:0000:0001")
    assert r["compressed"] == "2001:db8::1"
    assert r["exploded"] == "2001:0db8:0000:0000:0000:0000:0000:0001"


def test_convert_address_form_strips_a_prefix():
    assert ipt.convert_address_form("2001:db8::1/64")["compressed"] == "2001:db8::1"


def test_convert_address_form_rejects_bad_input():
    assert "Invalid IPv6 address" in ipt.convert_address_form("zzz")["error"]


# ---- IPv4 -> Hex -----------------------------------------------------------
def test_ipv4_to_hex():
    r = ipt.ipv4_to_hex("192.168.1.1")
    assert r["colon"] == "c0:a8:01:01"
    assert r["packed"] == "c0a80101"
    assert r["hexint"] == "0xC0A80101"
    assert r["decimal"] == 3232235777


def test_ipv4_to_hex_pads_low_octets():
    assert ipt.ipv4_to_hex("0.0.0.1")["colon"] == "00:00:00:01"


@pytest.mark.parametrize("text, fragment", [
    ("", "Enter an IPv4 address"),
    ("256.0.0.1", "Invalid IPv4 address"),
])
def test_ipv4_to_hex_errors(text, fragment):
    assert fragment in ipt.ipv4_to_hex(text)["error"]


# ---- IPv4-in-IPv6 embeddings ----------------------------------------------
def test_ipv4_to_ipv6_embeddings():
    # Python's ipaddress renders these in hex, not the dotted ::ffff:1.2.3.4
    # form, so the expected values below are hex too.
    r = ipt.ipv4_to_ipv6("192.168.1.1")
    assert r["nat64"] == "64:ff9b::c0a8:101"
    assert r["mapped"] == "::ffff:c0a8:101"
    assert r["sixto4"] == "2002:c0a8:101::/48"
    assert r["compat"] == "::c0a8:101"


def test_ipv4_to_ipv6_embeddings_carry_the_right_bits():
    r = ipt.ipv4_to_ipv6("192.168.1.1")
    iv = int(ipaddress.IPv4Address("192.168.1.1"))
    assert ipaddress.IPv6Address(r["mapped"]) == ipaddress.IPv6Address("::ffff:192.168.1.1")
    assert int(ipaddress.IPv6Address(r["nat64"])) - iv == int(ipaddress.IPv6Address("64:ff9b::"))
    assert ipaddress.IPv6Address(r["compat"]) == ipaddress.IPv6Address(iv)


def test_ipv4_to_ipv6_rejects_bad_input():
    assert "Invalid IPv4 address" in ipt.ipv4_to_ipv6("nope")["error"]


# ---- Embed IPv4 in an IPv6 prefix -----------------------------------------
def test_embed_places_ipv4_in_the_low_32_bits():
    r = ipt.embed_ipv4_in_prefix("fd2b:1a9c:7e3f::/48", "172.31.16.1")
    combined = ipaddress.IPv6Address(r["combined_hex"])
    assert int(combined) & 0xFFFFFFFF == int(ipaddress.IPv4Address("172.31.16.1"))
    assert r["hex_colon"] == "ac:1f:10:01"
    assert r["hex_packed"] == "ac1f1001"


def test_embed_mixed_notation_parses_back_to_the_same_address():
    r = ipt.embed_ipv4_in_prefix("fd2b:1a9c:7e3f::/48", "172.31.16.1")
    assert ipaddress.IPv6Address(r["combined_v4"]) == \
        ipaddress.IPv6Address(r["combined_hex"])


def test_embed_doc_example_is_in_the_documentation_range():
    r = ipt.embed_ipv4_in_prefix("fd2b:1a9c:7e3f::/48", "172.31.16.1")
    doc = ipaddress.IPv6Address(r["doc_hex"])
    assert doc in ipaddress.ip_network("2001:db8::/32")
    assert ipaddress.IPv6Address(r["doc_v4"]) == doc


@pytest.mark.parametrize("prefix, ipv4, fragment", [
    ("", "192.168.1.1", "Enter an IPv6 prefix"),
    ("fd2b::/48", "", "Enter an IPv4 address"),
    ("192.168.1.0/24", "192.168.1.1", "Prefix must be IPv6"),
    ("zzz/48", "192.168.1.1", "Invalid IPv6 prefix"),
    ("fd2b::/48", "999.1.1.1", "Invalid IPv4 address"),
])
def test_embed_errors(prefix, ipv4, fragment):
    assert fragment in ipt.embed_ipv4_in_prefix(prefix, ipv4)["error"]


# ---- Display scaling -------------------------------------------------------
class FakeWindow:
    """Stands in for a Tk window; only the DPI query is needed."""

    def __init__(self, dpi):
        self._dpi = dpi

    def winfo_fpixels(self, _spec):
        return self._dpi


@pytest.fixture
def linux(monkeypatch):
    monkeypatch.setattr(ipt.sys, "platform", "linux")
    monkeypatch.delenv(ipt.SCALING_ENV_VAR, raising=False)


@pytest.mark.parametrize("dpi, expected", [
    (96, None),        # standard DPI -- leave CustomTkinter alone
    (72, None),        # below baseline -- never shrink
    (144, 1.5),
    (192, 2.0),
    (960, 3.0),        # implausible DPI is clamped
])
def test_detect_scaling_from_dpi(linux, dpi, expected):
    got = ipt.detect_scaling(FakeWindow(dpi))
    if expected is None:
        assert got is None
    else:
        assert got == pytest.approx(expected, abs=0.01)


@pytest.mark.parametrize("platform", ["win32", "darwin"])
def test_detect_scaling_defers_to_customtkinter(monkeypatch, platform):
    monkeypatch.setattr(ipt.sys, "platform", platform)
    monkeypatch.delenv(ipt.SCALING_ENV_VAR, raising=False)
    assert ipt.detect_scaling(FakeWindow(192)) is None


def test_env_var_overrides_detection(monkeypatch):
    monkeypatch.setenv(ipt.SCALING_ENV_VAR, "1.25")
    # Wins even on Windows, and without consulting the window at all.
    monkeypatch.setattr(ipt.sys, "platform", "win32")
    assert ipt.detect_scaling(None) == pytest.approx(1.25)


@pytest.mark.parametrize("value, expected", [("0.1", 0.5), ("9", 4.0)])
def test_env_var_is_clamped(monkeypatch, value, expected):
    monkeypatch.setenv(ipt.SCALING_ENV_VAR, value)
    assert ipt.detect_scaling(None) == pytest.approx(expected)


def test_bad_env_var_falls_back_to_detection(linux, monkeypatch, capsys):
    monkeypatch.setenv(ipt.SCALING_ENV_VAR, "huge")
    assert ipt.detect_scaling(FakeWindow(144)) == pytest.approx(1.5, abs=0.01)
    assert "Ignoring" in capsys.readouterr().err


# ---- Mixed-notation helper -------------------------------------------------
@pytest.mark.parametrize("addr", [
    "fd2b:1a9c:7e3f::ac1f:1001",
    "2001:db8::c0a8:101",
    "::ffff:c0a8:101",
    "2001:db8:1:2:3:4:c0a8:101",
])
def test_ipv6_mixed_always_round_trips(addr):
    combined = ipaddress.IPv6Address(addr)
    v4 = ipaddress.IPv4Address(int(combined) & 0xFFFFFFFF)
    assert ipaddress.IPv6Address(ipt._ipv6_mixed(combined, v4)) == combined
