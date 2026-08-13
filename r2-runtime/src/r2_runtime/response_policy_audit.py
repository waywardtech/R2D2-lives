"""Offline, non-importing audit of the pinned spherov2 response policy."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any


_SOURCES = {
    "packet_manager": Path("controls/v2.py"),
    "toy_transport": Path("toy/__init__.py"),
    "drive_commands": Path("commands/drive.py"),
}


def _function(tree: ast.AST, class_name: str, function_name: str) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == function_name:
                    return child
    raise ValueError(f"missing expected {class_name}.{function_name} source boundary")


def _source(function: ast.FunctionDef, text: str) -> str:
    segment = ast.get_source_segment(text, function)
    if segment is None:
        raise ValueError("could not isolate expected source boundary")
    return segment


def audit_response_policy(package_root: Path, *, distribution_version: str) -> dict[str, Any]:
    """Describe client behavior without importing the package or accessing BLE."""
    if distribution_version != "0.12.1":
        raise ValueError("response-policy audit requires pinned spherov2 0.12.1")
    texts: dict[str, str] = {}
    hashes: dict[str, str] = {}
    trees: dict[str, ast.Module] = {}
    for label, relative in _SOURCES.items():
        path = package_root / relative
        data = path.read_bytes()
        texts[label] = data.decode("utf-8")
        hashes[label] = hashlib.sha256(data).hexdigest()
        trees[label] = ast.parse(texts[label], filename=relative.as_posix())

    new_packet = _source(
        _function(trees["packet_manager"], "Manager", "new_packet"), texts["packet_manager"]
    )
    execute = _source(_function(trees["toy_transport"], "Toy", "_execute"), texts["toy_transport"])
    wait_packet = _source(
        _function(trees["toy_transport"], "Toy", "_wait_packet"),
        texts["toy_transport"],
    )
    raw_motors = _source(
        _function(trees["drive_commands"], "Drive", "set_raw_motors"),
        texts["drive_commands"],
    )

    checks = {
        "packet_requests_response": "Packet.Flags.requests_response" in new_packet,
        "execute_enqueues_packet": "self.__packet_queue.put(packet.build())" in execute,
        "execute_waits_for_matching_id": "self._wait_packet(packet.id)" in execute,
        "wait_timeout_seconds": 10.0 if "timeout=10.0" in wait_packet else None,
        "raw_motor_uses_execute": "toy._execute(Drive._encode" in raw_motors,
        "raw_motor_did": 22 if "_did = 22" in texts["drive_commands"] else None,
        "raw_motor_cid": 1 if "Drive._encode(toy, 1," in raw_motors else None,
    }
    if not all(value is not None and value is not False for value in checks.values()):
        raise ValueError("pinned response-policy source shape did not match reviewed invariants")
    return {
        "schema_version": 1,
        "audit_kind": "spherov2.client_response_policy",
        "distribution": "spherov2",
        "distribution_version": distribution_version,
        "method": "static_ast_no_import_no_ble",
        "source_sha256": hashes,
        "checks": checks,
        "conclusion": "client_requires_matching_response_for_raw_motor_command",
        "firmware_behavior": "unverified",
        "movement_performed": False,
    }


def write_immutable_audit(output: Path, payload: dict[str, Any]) -> None:
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")
