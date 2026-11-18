import sys

# On Windows, piped/redirected stdout uses cp1252, so printing characters like
# "→" or "✓" raises UnicodeEncodeError and kills the request. Force UTF-8.
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
