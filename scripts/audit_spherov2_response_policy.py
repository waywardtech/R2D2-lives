from __future__ import annotations

import argparse
from pathlib import Path

from r2_runtime.response_policy_audit import audit_response_policy, write_immutable_audit


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline audit of pinned spherov2 response policy")
    parser.add_argument("--package-root", required=True, type=Path)
    parser.add_argument("--distribution-version", default="0.12.1")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    payload = audit_response_policy(
        args.package_root, distribution_version=args.distribution_version
    )
    write_immutable_audit(args.output, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
