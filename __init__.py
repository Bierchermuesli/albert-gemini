# -*- coding: utf-8 -*-
"""
Interact with Google's Gemini models.

Synopsis: <trigger> <query>
- Press Enter on the "Ask Gemini" item to generate a response (copied to clipboard + notification).
- End your query with '!' to fetch the response immediately and display it in the list.
"""

from albert import *
from pathlib import Path
from google import genai
from google.genai import types
import threading
import time
import shutil
import subprocess

LIVE_DEBOUNCE_SECONDS = 0.5

md_iid = "5.0"
md_version = "1.7"
md_name = "Gemini"
md_description = "Interact with Google Gemini"
md_license = "MIT"
md_url = ""
md_maintainers = ["@gemini"]
md_authors = ["@gemini"]
md_lib_dependencies = ["google-genai"]

class Plugin(PluginInstance, GeneratorQueryHandler):
    _api_key = ""
    _model_name = "gemini-2.0-flash"
    _system_instruction = ""
    
    DEFAULT_SYSTEM_PROMPT = (
        "You are an assistant running in a quick launcher. "
        "Keep answers extremely concise, precise, and short. "
        "Avoid markdown formatting like bold or italic unless necessary. "
        "Plain text is preferred."
    )

    def __init__(self):
        GeneratorQueryHandler.__init__(self)
        PluginInstance.__init__(self)
        self.icon_path = Path(__file__).parent / "icon.svg"
        self.client = None
        self._init_error = None
        
        self._init_configuration()

    @property
    def api_key(self):
        return self._api_key

    @api_key.setter
    def api_key(self, value):
        self._api_key = value
        self.writeConfig("api_key", value)
        self._setup_client()

    @property
    def model_name(self):
        return self._model_name

    @model_name.setter
    def model_name(self, value):
        self._model_name = value
        self.writeConfig("model_name", value)
        
    @property
    def system_instruction(self):
        return self._system_instruction

    @system_instruction.setter
    def system_instruction(self, value):
        self._system_instruction = value
        self.writeConfig("system_instruction", value)

    def _init_configuration(self):
        self._api_key = self.readConfig("api_key", str) or ""
        self._model_name = self.readConfig("model_name", str) or "gemini-2.0-flash"
        self._system_instruction = self.readConfig("system_instruction", str) or ""
        self._setup_client()

    def _setup_client(self):
        self._init_error = None
        if not self._api_key:
            self.client = None
            return

        try:
            self.client = genai.Client(api_key=self._api_key)
            info("Gemini: Client initialized successfully.")
        except Exception as e:
            self._init_error = f"Setup failed: {str(e)}"
            self.client = None
            warning(f"Failed to setup Gemini client: {e}")

    def configWidget(self):
        return [
            {
                "type": "label",
                "text": "Configure your Google Gemini API settings.",
            },
            {
                "type": "lineedit",
                "label": "API Key",
                "property": "api_key",
                "widget_properties": {"placeholderText": "AIzaSy..."}
            },
            {
                "type": "lineedit",
                "label": "Model Name",
                "property": "model_name",
                "widget_properties": {"placeholderText": "gemini-2.0-flash"}
            },
            {
                "type": "lineedit",
                "label": "System Instruction",
                "property": "system_instruction",
                "widget_properties": {"placeholderText": "Leave empty for default concise mode..."}
            },
            {
                "type": "label",
                "text": "Get your API key at <a href='https://aistudio.google.com/app/apikey'>Google AI Studio</a>.",
                "widget_properties": {"textFormat": "RichText", "openExternalLinks": True}
            }
        ]

    def defaultTrigger(self):
        return "gm "

    def synopsis(self, query):
        return "<query> (end with ! for live preview)"

    def _generate_content(self, query_text):
        if self._init_error:
            return f"Configuration Error: {self._init_error}"
        if not self.client:
            return "Configuration Error: Client not initialized. Check API Key."
            
        try:
            info(f"Gemini: Generating content for '{query_text}' using {self.model_name}...")
            
            instruction = self.system_instruction or self.DEFAULT_SYSTEM_PROMPT
            config = types.GenerateContentConfig(
                system_instruction=instruction
            )

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=query_text,
                config=config
            )
            
            if not response:
                return "Error: Empty response from API."
                
            info("Gemini: Content generated successfully.")
            
            # Direct text access
            if hasattr(response, 'text') and response.text:
                return response.text
                
            # Manual extraction for robust fallback
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    parts = candidate.content.parts
                    if parts:
                        return "".join([part.text for part in parts if part.text])
            
            return "Error: No text found in response."

        except Exception as e:
            warning(f"Gemini: Generation Error: {e}")
            return f"Generation Error: {str(e)}"

    # --- output channels --------------------------------------------------

    @staticmethod
    def _output_copy(text):
        setClipboardText(text)
        Notification(title="Gemini", text=text[:300]).send()

    @staticmethod
    def _output_paste(text):
        setClipboardText(text)
        helpers = [
            ("xdotool", ["xdotool", "key", "--clearmodifiers", "ctrl+v"]),
            ("wtype",   ["wtype", "-M", "ctrl", "v", "-m", "ctrl"]),
            ("ydotool", ["ydotool", "key", "29:1", "47:1", "47:0", "29:0"]),
        ]
        for binary, cmd in helpers:
            if shutil.which(binary):
                subprocess.Popen(
                    ["sh", "-c", f"sleep 0.15 && {' '.join(cmd)}"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                return
        if havePasteSupport():
            setClipboardTextAndPaste(text)
            return
        Notification(
            title="Gemini",
            text="Paste not available — install xdotool (X11) or wtype/ydotool (Wayland). Copied to clipboard.",
        ).send()

    @staticmethod
    def _output_notify(text):
        Notification(title="Gemini", text=text).send()

    @staticmethod
    def _output_copyq(text, question=""):
        if not shutil.which("copyq"):
            Notification(title="Gemini", text="copyq not installed; falling back to clipboard").send()
            setClipboardText(text)
            return
        note = f"gemini:{question}" if question else "gemini"
        try:
            subprocess.run(
                ["copyq", "write", "0",
                 "application/x-copyq-item-notes", note,
                 "text/plain", text],
                check=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            Notification(title="Gemini", text=f"Added to CopyQ history\n{text[:200]}").send()
        except Exception as e:
            warning(f"Gemini: copyq add failed: {e}")
            setClipboardText(text)

    def _async_send(self, query_text, output_fn):
        """Run generate_content in a daemon thread, then invoke output_fn(text)."""
        def _run():
            Notification(title="Gemini", text=f"Asking {self.model_name}...").send()
            text = self._generate_content(query_text)
            output_fn(text)
        threading.Thread(target=_run, daemon=True).start()

    def _icon(self, fallback=None):
        if self.icon_path.exists():
            return Icon.image(str(self.icon_path))
        return Icon.standard(fallback or Icon.StandardIconType.MediaPlay)

    def items(self, ctx):
        query_text = ctx.query.strip()

        if self._init_error:
            yield [StandardItem(
                id="gemini-init-error",
                text="Initialization Error",
                subtext=self._init_error,
                icon_factory=lambda: self._icon(Icon.StandardIconType.MessageBoxCritical),
                actions=[Action("settings", "Open Settings", lambda: openConfig())]
            )]
            return

        if not self.api_key:
            yield [StandardItem(
                id="gemini-no-key",
                text="API Key Missing",
                subtext="Please configure the API Key in the settings.",
                icon_factory=lambda: self._icon(Icon.StandardIconType.MessageBoxWarning),
                actions=[Action("settings", "Open Settings", lambda: openConfig())]
            )]
            return

        if not query_text:
            yield [StandardItem(
                id="gemini-idle",
                text="Gemini",
                subtext=f"Ready to query {self.model_name}",
                icon_factory=lambda: self._icon()
            )]
            return

        # Live mode: trailing "!" fires the API in-line. Debounce so rapid
        # typing doesn't burn quota; abort if query already moved on.
        if query_text.endswith("!"):
            real_query = query_text[:-1].strip()
            if not real_query:
                return

            yield [StandardItem(
                id="gemini-thinking",
                text="Thinking...",
                subtext=f"Querying {self.model_name}...",
                icon_factory=lambda: self._icon()
            )]
            time.sleep(LIVE_DEBOUNCE_SECONDS)
            if not ctx.isValid:
                return

            response_text = self._generate_content(real_query)
            if not ctx.isValid:
                return

            yield [StandardItem(
                id="gemini-result",
                text=response_text,
                subtext=f"Response from {self.model_name}",
                icon_factory=lambda: self._icon(),
                actions=[
                    Action("copy", "Copy + notify",
                           lambda t=response_text: self._output_copy(t)),
                    Action("paste", "Paste at cursor",
                           lambda t=response_text: self._output_paste(t)),
                    Action("copyq", "Add to CopyQ history",
                           lambda t=response_text, q=real_query: self._output_copyq(t, q)),
                    Action("notify", "Show notification",
                           lambda t=response_text: self._output_notify(t)),
                ]
            )]
        else:
            yield [StandardItem(
                id="gemini-ask",
                text="Ask Gemini",
                subtext=f"Enter: copy + notify · {self.model_name}",
                icon_factory=lambda: self._icon(),
                actions=[
                    Action("send-copy", "Copy + notify",
                           lambda q=query_text: self._async_send(q, self._output_copy)),
                    Action("send-paste", "Paste at cursor",
                           lambda q=query_text: self._async_send(q, self._output_paste)),
                    Action("send-copyq", "Add to CopyQ history",
                           lambda q=query_text: self._async_send(q, lambda t, qq=q: self._output_copyq(t, qq))),
                    Action("send-notify", "Notification only",
                           lambda q=query_text: self._async_send(q, self._output_notify)),
                ]
            )]
