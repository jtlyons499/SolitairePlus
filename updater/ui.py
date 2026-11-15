"""The updater window (tkinter, part of Python's standard library).

The update itself runs on a background thread (core.run_update). Every
question to the player is sent to the window thread and the worker waits for
the answer, so the window never freezes.
"""
from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import ttk

TITLE = "Solitaire+ Updater"
RED = "#b3261e"


class TkUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(TITLE)
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)  # closing mid-update could leave a half-copied file
        frame = ttk.Frame(self.root, padding=18)
        frame.pack(fill="both", expand=True)
        self.label = ttk.Label(frame, text="Starting…", width=58, wraplength=440)
        self.label.pack(anchor="w")
        self.bar = ttk.Progressbar(frame, length=440, mode="indeterminate")
        self.bar.pack(pady=(12, 0))
        self.bar.start(12)
        self.calls: queue.Queue = queue.Queue()
        self.root.after(50, self._pump)
        self.finished = threading.Event()

    # -------------------------------------------------------------- thread plumbing
    def _pump(self):
        while True:
            try:
                function, args, reply = self.calls.get_nowait()
            except queue.Empty:
                break
            value = function(*args)
            if reply is not None:
                reply.put(value)
        self.root.after(50, self._pump)

    def _call(self, function, *args, wait=False):
        reply = queue.Queue() if wait else None
        self.calls.put((function, args, reply))
        return reply.get() if wait else None

    def run(self, worker):
        """Run worker(ui) on a background thread; keep the window responsive until it finishes."""
        result = {}

        def target():
            result["code"] = worker(self)
            self._call(self.root.destroy)

        threading.Thread(target=target, daemon=True).start()
        self.root.mainloop()
        return result.get("code", 1)

    # -------------------------------------------------------------- core.py interface
    def status(self, text):
        self._call(self.label.configure, {"text": text})

    def progress(self, fraction):
        self._call(self._set_progress, fraction)

    def _set_progress(self, fraction):
        if fraction is None:
            if str(self.bar.cget("mode")) != "indeterminate":
                self.bar.configure(mode="indeterminate")
                self.bar.start(12)
        else:
            if str(self.bar.cget("mode")) != "determinate":
                self.bar.stop()
                self.bar.configure(mode="determinate", maximum=1000)
            self.bar["value"] = max(0, min(1000, int(fraction * 1000)))

    def done(self, text):
        self._call(self._message, "Update status", text, False, wait=True)

    def error(self, text):
        self._call(self._message, "Update failed", text, True, wait=True)

    def retry_locked(self, files):
        shown = "\n".join(f"  {name}" for name in files[:6]) + ("\n  …" if len(files) > 6 else "")
        return self._call(self._ask_retry, shown, wait=True)

    def confirm_unverified(self, details):
        if not self._call(self._warning_one, details, wait=True):
            return False
        return self._call(self._warning_two, wait=True)

    # -------------------------------------------------------------- dialogs (window thread)
    def _dialog(self, title):
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.lift()
        dialog.focus_force()
        return dialog

    def _wait(self, dialog, answer, default):
        dialog.protocol("WM_DELETE_WINDOW", lambda: (answer.__setitem__(0, default), dialog.destroy()))
        self.root.wait_window(dialog)
        return answer[0]

    def _message(self, title, text, is_error):
        self.bar.stop()
        dialog = self._dialog(title)
        frame = ttk.Frame(dialog, padding=18)
        frame.pack()
        tk.Label(frame, text=text, wraplength=440, justify="left",
                 fg=RED if is_error else "black").pack(anchor="w")
        button = ttk.Button(frame, text="Close", command=dialog.destroy)
        button.pack(anchor="e", pady=(14, 0))
        button.focus_set()
        dialog.bind("<Return>", lambda _e: dialog.destroy())
        self.root.wait_window(dialog)

    def _ask_retry(self, shown):
        dialog = self._dialog("Close Solitaire+ first")
        answer = [False]
        frame = ttk.Frame(dialog, padding=18)
        frame.pack()
        ttk.Label(frame, wraplength=440, justify="left", text=(
            "Some game files are still in use, so they can't be replaced yet:\n\n" + shown +
            "\n\nPlease close every Solitaire+ window (including the Multiplayer window), then click Retry."
        )).pack(anchor="w")
        buttons = ttk.Frame(frame)
        buttons.pack(anchor="e", pady=(14, 0))
        ttk.Button(buttons, text="Cancel", command=lambda: (answer.__setitem__(0, False), dialog.destroy())).pack(side="right")
        retry = ttk.Button(buttons, text="Retry", command=lambda: (answer.__setitem__(0, True), dialog.destroy()))
        retry.pack(side="right", padx=(0, 8))
        retry.focus_set()
        return self._wait(dialog, answer, False)

    def _warning_one(self, details):
        dialog = self._dialog("Update could not be verified")
        answer = [False]
        frame = ttk.Frame(dialog, padding=18)
        frame.pack()
        tk.Label(frame, text="This update could not be verified", fg=RED,
                 font=("Segoe UI", 13, "bold")).pack(anchor="w")
        tk.Label(frame, wraplength=480, justify="left", text=(
            "This update could not be verified as coming from the Solitaire+ developers. "
            "Nothing has been changed yet. We strongly recommend contacting the game's creator "
            "before installing."
        )).pack(anchor="w", pady=(8, 8))
        box = tk.Text(frame, width=66, height=9, wrap="word", font=("Consolas", 9))
        box.insert("1.0", details)
        box.configure(state="disabled")
        box.pack()
        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", pady=(14, 0))

        def copy():
            self.root.clipboard_clear()
            self.root.clipboard_append(details)

        ttk.Button(buttons, text="Continue anyway…",
                   command=lambda: (answer.__setitem__(0, True), dialog.destroy())).pack(side="left")
        ttk.Button(buttons, text="Copy details", command=copy).pack(side="right", padx=(8, 0))
        cancel = ttk.Button(buttons, text="Cancel", command=lambda: (answer.__setitem__(0, False), dialog.destroy()))
        cancel.pack(side="right")
        cancel.focus_set()  # Cancel is the default
        dialog.bind("<Return>", lambda _e: (answer.__setitem__(0, False), dialog.destroy()))
        dialog.bind("<Escape>", lambda _e: (answer.__setitem__(0, False), dialog.destroy()))
        return self._wait(dialog, answer, False)

    def _warning_two(self):
        dialog = self._dialog("Are you sure?")
        answer = [False]
        understood = tk.BooleanVar(value=False)
        frame = ttk.Frame(dialog, padding=18)
        frame.pack()
        tk.Label(frame, text="Are you sure?", fg=RED, font=("Segoe UI", 13, "bold")).pack(anchor="w")
        tk.Label(frame, wraplength=460, justify="left", text=(
            "Installing an unverified update could run software that did not come from the "
            "Solitaire+ developers. Only continue if the game's creator has told you the signing "
            "certificate changed."
        )).pack(anchor="w", pady=(8, 8))
        # Created in reading order so Tab moves: checkbox -> Install -> Cancel.
        controls = {}
        ttk.Checkbutton(frame, text="I understand the risk", variable=understood,
                        command=lambda: controls["install"].configure(
                            state="normal" if understood.get() else "disabled")
                        ).pack(anchor="w")
        buttons = ttk.Frame(frame)
        install = ttk.Button(buttons, text="Install unverified update", state="disabled",
                             command=lambda: (answer.__setitem__(0, True), dialog.destroy()))
        controls["install"] = install
        buttons.pack(fill="x", pady=(14, 0))
        cancel = ttk.Button(buttons, text="Cancel", command=lambda: (answer.__setitem__(0, False), dialog.destroy()))
        cancel.pack(side="right")
        install.pack(side="left")
        cancel.focus_set()
        dialog.bind("<Escape>", lambda _e: (answer.__setitem__(0, False), dialog.destroy()))
        return self._wait(dialog, answer, False)
