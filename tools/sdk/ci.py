"""Build, test and package the browser SDK with explicit actual command evidence."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import sys

from shared import ROOT, engine_version, json_bytes


BUILD = ROOT / "Build"
EVIDENCE = BUILD / "sdk-ci-evidence.json"


def annotation(message: str) -> str:
    return message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


class Runner:
    def __init__(self) -> None:
        self.results: list[dict] = []
        BUILD.mkdir(exist_ok=True)
        self.logs = BUILD / "sdk-ci-logs"
        self.logs.mkdir(exist_ok=True)

    def save(self) -> None:
        EVIDENCE.write_bytes(json_bytes(self.results))

    def run(self, command: list[str], cwd: Path = ROOT) -> None:
        display = shlex.join(command)
        actual = list(command)
        if actual[0] == "npm":
            # Arguments are fixed by this script. No user-supplied command text
            # is evaluated through a shell; Windows uses its installed npm.cmd.
            executable = shutil.which("npm.cmd" if os.name == "nt" else "npm")
            if executable is None:
                raise RuntimeError("Node.js 24 with npm must be installed before SDK CI")
            actual[0] = executable
        log = self.logs / f"command-{len(self.results):02}.log"
        print(f"Running: {display}", flush=True)
        with log.open("w", encoding="utf-8", newline="\n") as stream:
            process = subprocess.Popen(
                actual, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace",
            )
            assert process.stdout is not None
            for line in process.stdout:
                print(line, end="", flush=True)
                stream.write(line)
            status = process.wait()
        self.results.append({
            "command": display,
            "working_directory": str(cwd.relative_to(ROOT)) or ".",
            "exit_code": status,
            "platform": platform.platform(),
        })
        self.save()
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with Path(summary).open("a", encoding="utf-8") as stream:
                stream.write(f"- Exit {status}: `{display}`\n")
        if status:
            tail = "\n".join(log.read_text(encoding="utf-8").splitlines()[-45:])
            print("::error::" + annotation(f"Failed ({status}): {display}\n{tail}"), flush=True)
            raise RuntimeError(f"SDK command failed ({status}): {display}")


def at_exact_tag() -> bool:
    tag = f"v{engine_version()}^{{commit}}"
    tagged = subprocess.run(["git", "rev-parse", tag], cwd=ROOT, capture_output=True, text=True)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    return tagged.returncode == 0 and tagged.stdout.strip() == head


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--with-browser-deps", action="store_true", help="Install Playwright Linux system dependencies on the GitHub runner")
    arguments = parser.parse_args()
    os.environ["PYTHON"] = sys.executable
    os.environ.setdefault("SDK_BACKENDS", "webgl2")
    runner = Runner()
    runner.run(["node", "--version"])
    runner.run(["npm", "ci", "--prefix", "tools/browser"])
    install = ["npm", "--prefix", "tools/browser", "exec", "--", "playwright", "install", "chromium"]
    if arguments.with_browser_deps:
        install.append("--with-deps")
    runner.run(install)
    runner.run([sys.executable, "tools/sdk/build.py"])
    runner.run(["npm", "--prefix", "tools/browser", "run", "types"])
    runner.run(["npm", "--prefix", "tools/browser", "run", "unit"])
    runner.run(["npm", "test"], ROOT / "tools/browser")
    report = json.loads((BUILD / "sdk-browser-results.json").read_text(encoding="utf-8"))
    stats = report["stats"]
    if stats.get("expected", 0) < 1 or any(stats.get(field, 0) for field in ["unexpected", "skipped", "flaky"]):
        raise RuntimeError("SDK release requires passing browser tests without failures, skips or flaky outcomes")
    runner.results[-1]["browser_test_stats"] = stats
    runner.results[-1]["requested_backend_projects"] = [project["name"] for project in report["config"]["projects"]]
    runner.save()
    package = [sys.executable, "tools/sdk/pack.py", "--evidence", str(EVIDENCE)]
    if not at_exact_tag():
        package.append("--candidate")
    # The archive includes evidence of the preceding tests. Recording packaging
    # itself inside that same archive would make its evidence self-referential.
    subprocess.run(package, cwd=ROOT, check=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("::error::" + annotation(str(error)), flush=True)
        raise
