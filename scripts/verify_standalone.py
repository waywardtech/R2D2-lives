"""Run each product test suite in a copy where the peer source is absent."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]

for project, peer in (("r2-runtime", "bat-space-modeler"), ("bat-space-modeler", "r2-runtime")):
    with tempfile.TemporaryDirectory(prefix=f"sap-{project}-") as raw_temp:
        temp = Path(raw_temp)
        shutil.copytree(ROOT / "protocol", temp / "protocol")
        shutil.copytree(ROOT / project, temp / project)
        assert not (temp / peer).exists()
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join(
            (str(temp / "protocol" / "src"), str(temp / project / "src"))
        )
        subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", f"{project}/tests", "-v"],
            cwd=temp,
            env=env,
            check=True,
        )
        print(f"{project}: standalone tests passed with {peer} absent")

