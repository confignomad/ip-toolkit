# IP Toolkit

> **Version 0.7.0 (alpha)**

A dark-themed desktop app bundling seven small **IPv6 / IPv4 networking tools** into
one window — subnet math, random address generation, conversions, and IPv4-in-IPv6
embeddings. Built to be *useful and educational*: results come with plain-English
notes and the relevant RFC references.

> Built with Python + [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter).
> All address math uses the Python standard library (`ipaddress`) — no heavyweight
> dependencies.

![IP Toolkit screenshot](docs/screenshot.png)

## Features

Pick a tool from the **Tools** menu; each swaps the input row and shares one output box.
The app opens on the **IPv6 Calculator**.

| Tool | What it does |
|------|--------------|
| **IPv6 Calculator** | Network address, first/last address, prefix length, total count, compressed + exploded forms. |
| **IPv4 Calculator** | Network ID, broadcast, netmask, wildcard, usable hosts, host range (handles `/31` and `/32`). |
| **Prefix Converter** | Prefix length → address count, hex netmask, and `/64` subnet count; plus compressed ↔ exploded address forms. |
| **Random Address Generator** | 1–100 random addresses per click, from your own prefix, documentation space (`2001:db8::/32`) or ULA space (`fd00::/8`). The prefix field applies to **Host in prefix** mode only and takes an IPv6 network; blank → global unicast (`2000::/4`). |
| **IPv4 → Hex** | An IPv4 address as colon-hex (`c0:a8:01:01`), packed hex, `0x` form, and decimal. |
| **IPv4-in-IPv6 Embeddings** | How an IPv4 address is embedded in IPv6: **NAT64** (current) and IPv4-mapped, plus the deprecated 6to4 / IPv4-compatible forms — with an explanation that this isn't a real "conversion." |
| **Embed IPv4 in Prefix** | Place an IPv4 into an IPv6 prefix's low 32 bits, shown in hex and dotted-IPv4 forms, with a live documentation-range example. |

### Design highlights
- **Guard rail — never enumerates.** IPv6 networks can hold quintillions of addresses,
  so the app only *indexes* (`net[0]`, `net[-1]`, a random index) and reads
  `net.num_addresses`. It never builds an address list, so it can't hang or exhaust memory.
- **Dark UI** — the app itself is dark throughout; the native menu bar follows your
  OS theme, so it may appear light (as in the screenshot above).
- **No pop-ups** — the `≡` menu (About / Python Libraries / GitHub / RFC References,
  plus Exit) prints into the shared output box.
- **Teaches as it works** — e.g. the ULA generator explains why only `fd00::/8` is usable.

## Requirements

- **Python 3.9+** (developed and tested on 3.12)
- **CustomTkinter** (installed via `requirements.txt`; everything else — `ipaddress`,
  `random`, `tkinter` — ships with Python)
- **Linux only:** some distributions ship Python without `tkinter`. On Debian/Ubuntu,
  install it with `sudo apt install python3-tk`.

## Installation & Usage

```bash
# 1. Clone
git clone https://github.com/confignomad/ip-toolkit.git
cd ip-toolkit

# 2. (Recommended) create a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 3. Install dependencies (CustomTkinter to run, pytest for development)
pip install -r requirements.txt

# 4. Run
python ip-toolkit.py
```

## Testing

The address math lives in plain functions with no GUI code, so the suite runs
headlessly (no display needed):

```bash
pytest
```

`tests/test_ip_toolkit.py` covers all seven tools' logic — subnet math, the
`/31` and `/32` edge cases, generator ranges, the IPv4-in-IPv6 embeddings, and
the mixed hex/dotted notation round-trip — plus every error path.

## Tips
- Press **Enter** in any input field to run the current tool — no need to reach for
  the button. Every tool also has a **Clear** button that empties the output box.
- On **Windows and Linux**, every input field supports **Cut / Copy / Paste /
  Select All** via right-click, plus the usual Ctrl+X/C/V and Ctrl+A.
- Use the **documentation** generator (`2001:db8::/32`, RFC 3849) for examples,
  screenshots, and teaching — those addresses are reserved and never routed.

## Standards referenced
RFC 8200 (IPv6), 4291 (addressing), 5952 (text representation), 4193 (ULA),
3849 (documentation), 6052 (NAT64), 3056 (6to4), 7526 (6to4 deprecation),
4632 (CIDR).

## Author
Developed and designed by **Ron Staples**.

## License
No license is set yet. Until one is added, all rights are reserved — if you'd like
others to reuse it, consider adding an [MIT](https://choosealicense.com/licenses/mit/)
or similar license.
