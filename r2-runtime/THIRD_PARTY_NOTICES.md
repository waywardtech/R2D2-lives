# Third-party notices

## spherov2 0.12.1

- Project: `spherov2.py`, an unofficial Sphero BLE library
- Upstream: <https://github.com/artificial-intelligence-class/spherov2.py>
- PyPI source: <https://pypi.org/project/spherov2/0.12.1/>
- Source SHA-256: `087929a28164af78c8a258396593a51d45fc89af23e86c524d86d0a5d094908f`
- License: MIT
- Copyright: 2020 University of Pennsylvania

The dependency is not vendored here. Its license must remain present in any
installed distribution or bundled release. This project uses a narrow owned
adapter and does not expose upstream low-level packet or motor APIs.

## Bleak 0.21.1

- Project: Bleak
- Upstream: <https://github.com/hbldh/bleak>
- PyPI: <https://pypi.org/project/bleak/0.21.1/>
- Source SHA-256: `ec4a1a2772fb315b992cbaa1153070c7e26968a52b0e2727035f443a1af5c18f`
- License: MIT

Bleak 0.21.1 is the selected compatibility baseline for Python 3.11. It is not
installed by default and remains subject to target-Pi import verification and HIL.

## Locked runtime dependencies

The target-Pi lock also contains the following unvendored wheels. Exact artifact
names, versions, sizes, and SHA-256 hashes are in
`hardware-wheelhouse.manifest.json`.

- `dbus-fast` 2.46.4 — MIT
- `numpy` 1.26.4 — BSD-3-Clause
- `transforms3d` 0.4.1 — BSD license
- `typing-extensions` 4.16.0 — PSF-2.0

Redistributions must include each package's own license files. The checked
manifest is dependency evidence and does not substitute for those notices.
