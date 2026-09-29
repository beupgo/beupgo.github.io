#!/usr/bin/env python3
"""Publish the current artifacts as one root commit; never delete source branches."""

import argparse
import os
import subprocess
from pathlib import Path


def git(root: Path, *args: str, env: dict | None = None) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), *args], text=True, env=env
    ).strip()


def publish(root: Path, branch: str, expected_head: str) -> str:
    git(root, "check-ref-format", "refs/heads/" + branch)
    if git(root, "rev-parse", "HEAD") != expected_head:
        raise ValueError("Checkout changed; refusing to publish a different revision")
    git(root, "add", "--all")
    tree = git(root, "write-tree")
    identity = {
        "GIT_AUTHOR_NAME": "beupgo",
        "GIT_AUTHOR_EMAIL": "2108595+beupgo@users.noreply.github.com",
        "GIT_COMMITTER_NAME": "beupgo",
        "GIT_COMMITTER_EMAIL": "2108595+beupgo@users.noreply.github.com",
    }
    parents = git(root, "rev-list", "--parents", "-n", "1", expected_head).split()
    same_author = git(root, "show", "-s", "--format=%an <%ae>", expected_head) == (
        "beupgo <2108595+beupgo@users.noreply.github.com>"
    )
    if len(parents) == 1 and tree == git(root, "rev-parse", expected_head + "^{tree}") and same_author:
        snapshot = expected_head
    else:
        # No -p: this commit deliberately has no parents/history.
        snapshot = git(root, "commit-tree", tree, "-m", "Publish latest artifacts",
                       env={**os.environ, **identity})
    # The lease prevents overwriting a concurrent user push.
    git(root, "push", "--force-with-lease=refs/heads/" + branch + ":" + expected_head,
        "origin", snapshot + ":refs/heads/" + branch)
    print("Published artifact snapshot:", snapshot)
    return snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--expected-head", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    publish(root, args.branch, args.expected_head)


if __name__ == "__main__":
    main()
