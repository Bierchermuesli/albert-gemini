# Gemini — Albert Python Plugin

> **Experimental.** Personal hack, single maintainer. Expect rough edges, breaking changes, and unreviewed code paths. Use at your own risk.

Ask [Google Gemini](https://ai.google.dev/) from the [Albert Launcher](https://albertlauncher.github.io/). One-shot prompts without opening a chat window.

## Modes

| Trigger | Behaviour |
|---|---|
| `gm <prompt>` | Renders an "Ask Gemini" row. **Enter** sends async; the result lands as a notification with the response on the clipboard. Alt picks the output channel. |
| `gm <prompt>!` | **Live mode** — fires on typing (with a ~500ms debounce) and renders the response inline. |

## Output channels (Alt menu)

- **Copy + notify** — default. Copies the response and shows a notification.
- **Paste at cursor** — uses `xdotool` (X11), `wtype` or `ydotool` (Wayland), falling back to Albert's built-in paste support. Copies regardless so `Ctrl+V` works if synthesised paste fails.
- **Add to CopyQ history** — stashes the response in CopyQ with a `gemini:<question>` note, leaving your live clipboard intact. Falls back to plain clipboard if `copyq` isn't installed.
- **Notification only** — fire and forget; no clipboard pollution.

## Installation

```bash
pip install --user google-genai
git clone https://github.com/Bierchermuesli/albert-gemini.git \
  ~/.local/share/albert/python/plugins/albert-gemini
```

Then enable the plugin in Albert's Python Modules settings.

## Configuration

- **API Key** — get one at [Google AI Studio](https://aistudio.google.com/app/apikey).
- **Model** — default `gemini-2.0-flash`. Any model id accepted by the `google-genai` SDK works.
- **System instruction** — override the bundled launcher-tuned system prompt. Leave empty for the default (concise, plain-text answers).

## Cost notes

`!` (live mode) fires on typing — keep it on a fast/cheap model. The bare `gm <prompt>` form only fires on Enter.

## Bugs / Feedback

Always welcome.
