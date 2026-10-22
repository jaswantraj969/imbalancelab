#!/usr/bin/env bash
# Milestone gate: lint, format, type-check, tests with coverage. Prints each command and its
# real output; exits non-zero if any step fails.
set -u
status=0
run() {
  echo "\$ $*"
  "$@" 2>&1
  local rc=$?
  echo "[exit $rc]"
  echo
  [ $rc -eq 0 ] || status=1
}
run ruff check .
run ruff format --check .
run mypy
run pytest -q --cov=imbalancelab --cov-report=term-missing
exit $status
