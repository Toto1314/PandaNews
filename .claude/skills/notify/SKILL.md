---
name: notify
description: Send a Telegram message to your phone via the Kiriko bot. Pass any message as the argument.
allowed-tools: [Bash]
---

# Notify — Send Telegram Message

Send a message to the user's phone via Telegram bot Kiriko.

`$ARGUMENTS` is the message to send. If empty, ask what to send.

Run:
```bash
python ~/.claude/notify.py "$ARGUMENTS"
```

If `$ARGUMENTS` contains a `--title` flag, pass it through as-is.

Examples:
- `/notify "PLTR hit $78 — check entry condition"`
- `/notify --title "Portfolio Alert" "AMPX near 52-week high, consider trim"`
- `/notify "Build finished successfully"`

After running, confirm it was sent.
