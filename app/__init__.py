"""Autonomous Code & Analysis Workspace package."""

import sys

# On Windows, stdout/stderr default to the legacy cp1252 codepage when they are
# piped or redirected (uvicorn under a process manager, CI, IDE terminals...).
# Any print() containing characters like "→" or "✓" then raises
# UnicodeEncodeError and kills the request mid-workflow. Force UTF-8 and never
# let a log line crash the app.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
