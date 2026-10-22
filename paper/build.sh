#!/usr/bin/env bash
#
# build.sh — build main.pdf reproducibly.
#
# Replaces running `xelatex; bibtex; xelatex; xelatex` by hand. Three failure
# modes motivated this script:
#
#   1. Bare `xelatex main.tex` stops at the interactive `?` prompt on any
#      error and waits for the keyboard. Ctrl+C there kills the run while it
#      is writing main.aux, leaving a truncated \newlabel that makes every
#      later run fail with "File ended while scanning use of \@newl@bel".
#      -interaction=nonstopmode means it never waits, so there is nothing to
#      interrupt.
#   2. Two builds in the same directory (editor build-on-save plus a terminal
#      build) overwrite each other's main.aux. A lock directory prevents that.
#   3. Once main.aux is truncated it stays broken until deleted. This script
#      detects that and clears it automatically.
#
# Usage:
#   ./build.sh            # incremental build
#   ./build.sh --clean    # discard generated files first
#
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

JOB=main
GENERATED=("$JOB".aux "$JOB".bbl "$JOB".blg "$JOB".lof "$JOB".log "$JOB".lot \
           "$JOB".out "$JOB".toc "$JOB".synctex.gz)
LOCK=".${JOB}.build.lock"

# mkdir is atomic, so this is a real mutex rather than a test-then-write race.
if ! mkdir "$LOCK" 2>/dev/null; then
    echo "error: a build is already running (lock: $LOCK)." >&2
    echo "       If no build is active, remove it with: rmdir $LOCK" >&2
    exit 1
fi
trap 'rmdir "$LOCK" 2>/dev/null || true' EXIT

if [[ "${1:-}" == "--clean" ]]; then
    echo "==> cleaning generated files"
    rm -f "${GENERATED[@]}"
fi

# A truncated .aux is read back at \begin{document} and aborts the run, so
# check it before starting rather than after failing. An .aux from a completed
# run ends with \gdef \@abspage@last{...}.
if [[ -f "$JOB.aux" ]] && ! grep -q '@abspage@last' "$JOB.aux"; then
    echo "==> $JOB.aux is incomplete (previous run was interrupted); discarding"
    rm -f "$JOB.aux"
fi

# Left behind when a run dies before compressing its synctex index.
find . -maxdepth 1 -name '*.synctex(busy)' -delete

run_tex() {
    echo "==> xelatex ($1)"
    # -synctex=1 is required for PDF-to-source jumping in the editor; without
    # it the viewer loses forward and inverse search.
    # nonstopmode still exits 1 on error; we want to reach the log summary.
    xelatex -synctex=1 -interaction=nonstopmode -file-line-error "$JOB.tex" \
        > /dev/null || true
}

run_tex "pass 1"

echo "==> bibtex"
bibtex "$JOB" > "$JOB.bibtex.log" 2>&1 || true
if grep -q "didn't find a database entry" "$JOB.bibtex.log"; then
    echo "    warning: bibtex could not resolve some entries:"
    grep "didn't find a database entry" "$JOB.bibtex.log" | sed 's/^/      /'
fi

run_tex "pass 2"
run_tex "pass 3"

echo
echo "==> result"

status=0

if grep -q '^!' "$JOB.log"; then
    echo "    ERRORS:"
    grep -n '^!' "$JOB.log" | head -20 | sed 's/^/      /'
    status=1
fi

if grep -qE 'Warning.*(undefined|Undefined)' "$JOB.log"; then
    echo "    UNDEFINED references or citations:"
    grep -E 'Warning.*(undefined|Undefined)' "$JOB.log" | head -20 | sed 's/^/      /'
    status=1
fi

# Informational: these are typography nits, not failures.
overfull=$(grep -c 'Overfull \\hbox' "$JOB.log" || true)
echo "    overfull hboxes: ${overfull:-0}"

if [[ -f "$JOB.pdf" ]]; then
    echo "    $(grep -o 'Output written on .*' "$JOB.log" | tail -1)"
else
    echo "    ERROR: no $JOB.pdf produced"
    status=1
fi

if [[ $status -eq 0 ]]; then
    echo "    no errors, no undefined references"
fi

exit $status
