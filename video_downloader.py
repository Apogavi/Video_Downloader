#!/usr/bin/env python3
"""
Universal Video Downloader
--------------------------
A simple Tkinter GUI for downloading videos from YouTube, Reddit, X (Twitter),
Instagram, TikTok and ~1000 other sites, powered by yt-dlp.

Features:
  - Quality picker (defaults to 720p, great for memes / quick clips)
  - Audio-only mode (extracts MP3)
  - Download queue + history (persisted between sessions)
  - Browser-cookie login for sites that require authentication (Reddit, IG, X)
  - Auto-installs yt-dlp on first run

Just run:  python video_downloader.py
"""

import os
import sys
import json
import queue
import threading
import subprocess
import importlib
import shutil
from datetime import datetime

import tkinter as tk
from tkinter import ttk, filedialog, messagebox


# --------------------------------------------------------------------------- #
#  Dependency bootstrap
# --------------------------------------------------------------------------- #
def ensure_yt_dlp():
    """Import yt_dlp, installing it via pip on first run if necessary."""
    try:
        return importlib.import_module("yt_dlp")
    except ImportError:
        pass

    print("yt-dlp not found - installing (first run only)...")
    cmds = [
        [sys.executable, "-m", "pip", "install", "--user", "--upgrade", "yt-dlp"],
        [sys.executable, "-m", "pip", "install", "--user", "--break-system-packages",
         "--upgrade", "yt-dlp"],
    ]
    last_err = None
    for cmd in cmds:
        try:
            subprocess.check_call(cmd)
            importlib.invalidate_caches()
            return importlib.import_module("yt_dlp")
        except Exception as e:  # noqa: BLE001
            last_err = e
    raise RuntimeError(
        "Could not auto-install yt-dlp. Please run:\n"
        f"    {sys.executable} -m pip install --user yt-dlp\n\n"
        f"Original error: {last_err}"
    )


def ffmpeg_available():
    """ffmpeg is needed to merge HD streams and to create MP3s."""
    return shutil.which("ffmpeg") is not None


# --------------------------------------------------------------------------- #
#  Paths / history persistence
# --------------------------------------------------------------------------- #
APP_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(APP_DIR, "download_history.json")
# C:\Users\You\Videos\Video_downloader or ~/Videos/Video_downloader is a good default, but we'll let users pick their own folder.
DEFAULT_DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Videos", "Video_downloader")


def load_history():
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_history(history):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as fh:
            json.dump(history, fh, indent=2)
    except OSError:
        pass


# --------------------------------------------------------------------------- #
#  Quality presets -> yt-dlp format strings
# --------------------------------------------------------------------------- #
QUALITY_PRESETS = {
    "Best available":       "bestvideo+bestaudio/best",
    "1080p":                "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
    "720p (recommended)":   "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
    "480p":                 "bestvideo[height<=480]+bestaudio/best[height<=480]/best",
    "360p (smallest)":      "bestvideo[height<=360]+bestaudio/best[height<=360]/best",
    "Audio only (MP3)":     "bestaudio/best",
}

# Cookies are now automatically handled via cookies.txt in the application directory.


# --------------------------------------------------------------------------- #
#  Main application
# --------------------------------------------------------------------------- #
class VideoDownloaderApp:
    def __init__(self, root, yt_dlp_module):
        self.root = root
        self.yt_dlp = yt_dlp_module
        self.download_dir = DEFAULT_DOWNLOAD_DIR
        os.makedirs(self.download_dir, exist_ok=True)

        self.history = load_history()
        self.job_queue = queue.Queue()
        self.ui_queue = queue.Queue()          # messages from worker -> UI thread
        self.queue_items = {}                  # id -> tree iid mapping
        self.next_id = 0
        self.worker_busy = False

        self._build_ui()
        self._populate_history()

        threading.Thread(target=self._worker_loop, daemon=True).start()
        self.root.after(120, self._poll_ui_queue)

        if not ffmpeg_available():
            self._set_status(
                "Note: ffmpeg not found - HD merging & MP3 conversion may be limited. "
                "Install ffmpeg for best results."
            )

    # ----------------------------- UI ------------------------------------- #
    def _build_ui(self):
        self.root.title("Universal Video Downloader")
        self.root.geometry("820x580")
        self.root.minsize(700, 480)

        pad = {"padx": 8, "pady": 4}

        # --- URL row ---
        top = ttk.Frame(self.root)
        top.pack(fill="x", **pad)

        ttk.Label(top, text="Video URL:").pack(side="left")
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(top, textvariable=self.url_var)
        self.url_entry.pack(side="left", fill="x", expand=True, padx=6)
        self.url_entry.bind("<Return>", lambda e: self.add_to_queue())

        ttk.Button(top, text="Paste", command=self._paste).pack(side="left")
        ttk.Button(top, text="Add to Queue", command=self.add_to_queue).pack(
            side="left", padx=4)

        # --- options row ---
        opts = ttk.Frame(self.root)
        opts.pack(fill="x", **pad)

        ttk.Label(opts, text="Quality:").pack(side="left")
        self.quality_var = tk.StringVar(value="720p (recommended)")
        self.quality_box = ttk.Combobox(
            opts, textvariable=self.quality_var,
            values=list(QUALITY_PRESETS.keys()), state="readonly", width=22)
        self.quality_box.pack(side="left", padx=6)



        # --- folder row ---
        frow = ttk.Frame(self.root)
        frow.pack(fill="x", **pad)
        ttk.Label(frow, text="Save to:").pack(side="left")
        self.dir_var = tk.StringVar(value=self.download_dir)
        ttk.Entry(frow, textvariable=self.dir_var, state="readonly").pack(
            side="left", fill="x", expand=True, padx=6)
        ttk.Button(frow, text="Browse", command=self._choose_dir).pack(side="left")

        # --- queue table ---
        mid = ttk.LabelFrame(self.root, text="Download Queue")
        mid.pack(fill="both", expand=True, **pad)

        cols = ("title", "quality", "status")
        self.tree = ttk.Treeview(mid, columns=cols, show="headings", height=10)
        self.tree.heading("title", text="Title / URL")
        self.tree.heading("quality", text="Quality")
        self.tree.heading("status", text="Status")
        self.tree.column("title", width=440)
        self.tree.column("quality", width=130, anchor="center")
        self.tree.column("status", width=170, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)

        sb = ttk.Scrollbar(mid, orient="vertical", command=self.tree.yview)
        sb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=sb.set)

        # --- bottom controls ---
        bottom = ttk.Frame(self.root)
        bottom.pack(fill="x", **pad)
        ttk.Button(bottom, text="Open download folder",
                   command=self._open_folder).pack(side="left")
        ttk.Button(bottom, text="Clear finished",
                   command=self._clear_finished).pack(side="left", padx=6)

        self.progress = ttk.Progressbar(bottom, mode="determinate", maximum=100)
        self.progress.pack(side="left", fill="x", expand=True, padx=8)

        # --- status bar ---
        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(self.root, textvariable=self.status_var, relief="sunken",
                  anchor="w").pack(fill="x", side="bottom")

    # ------------------------- UI helpers --------------------------------- #
    def _paste(self):
        try:
            self.url_var.set(self.root.clipboard_get().strip())
        except tk.TclError:
            pass

    def _choose_dir(self):
        d = filedialog.askdirectory(initialdir=self.download_dir)
        if d:
            self.download_dir = d
            self.dir_var.set(d)



    def _open_folder(self):
        path = self.dir_var.get()
        os.makedirs(path, exist_ok=True)
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)  # noqa: SLF001
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception:  # noqa: BLE001
            messagebox.showinfo("Folder", f"Downloads are in:\n{path}")

    def _set_status(self, text):
        self.status_var.set(text)

    def _populate_history(self):
        for item in self.history[-50:]:
            self.tree.insert(
                "", "end",
                values=(item.get("title", item.get("url", "")),
                        item.get("quality", ""),
                        item.get("status", "done")))

    def _clear_finished(self):
        for iid in self.tree.get_children():
            status = self.tree.set(iid, "status")
            if status in ("Done", "done", "Error"):
                self.tree.delete(iid)
        self.history.clear()
        save_history(self.history)

    # ------------------------- queue logic -------------------------------- #
    def add_to_queue(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("No URL", "Please paste a video URL first.")
            return
        if not (url.startswith("http://") or url.startswith("https://")):
            messagebox.showwarning("Invalid URL", "That doesn't look like a link.")
            return

        quality_label = self.quality_var.get()
        job_id = self.next_id
        self.next_id += 1

        iid = self.tree.insert("", "end",
                               values=(url, quality_label, "Queued"))
        self.queue_items[job_id] = iid

        self.job_queue.put({
            "id": job_id,
            "url": url,
            "quality_label": quality_label,
            "fmt": QUALITY_PRESETS[quality_label],
            "audio_only": quality_label.startswith("Audio"),
            "outdir": self.download_dir,
        })
        self.url_var.set("")
        self._set_status(f"Added to queue: {url}")

    # ------------------------- worker thread ------------------------------ #
    def _worker_loop(self):
        while True:
            job = self.job_queue.get()
            self.worker_busy = True
            self._download(job)
            self.worker_busy = False
            self.job_queue.task_done()

    def _download(self, job):
        self.ui_queue.put(("status", job["id"], "Starting...", None))

        def hook(d):
            if d["status"] == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate")
                downloaded = d.get("downloaded_bytes", 0)
                pct = (downloaded / total * 100) if total else 0
                self.ui_queue.put(("progress", job["id"], f"{pct:4.1f}%", pct))
            elif d["status"] == "finished":
                self.ui_queue.put(("progress", job["id"], "Processing...", 100))

        outtmpl = os.path.join(job["outdir"], "%(title)s.%(ext)s")
        ydl_opts = {
            "outtmpl": outtmpl,
            "format": job["fmt"],
            "progress_hooks": [hook],
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
        }
        # Automatically use reddit_cookies.txt in the same folder if downloading from Reddit.
        if "reddit.com" in job["url"].lower():
            cookie_path = os.path.join(APP_DIR, "reddit_cookies.txt")
            if os.path.exists(cookie_path):
                ydl_opts["cookiefile"] = cookie_path
        if job["audio_only"]:
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]
        else:
            ydl_opts["merge_output_format"] = "mp4"

        title = job["url"]
        try:
            with self.yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(job["url"], download=True)
                title = info.get("title", job["url"]) if info else job["url"]
            self.ui_queue.put(("done", job["id"], "Done", title))
            self._record_history(job, title, "Done")
        except Exception as e:  # noqa: BLE001
            raw = str(e)
            msg = raw.splitlines()[0][:120]
            if "authentication" in raw.lower() or "cookies" in raw.lower():
                msg = ("Login required - ensure a valid 'cookies.txt' file "
                       "is placed in the same folder as this script.")
            self.ui_queue.put(("error", job["id"], f"Error: {msg}", title))
            self._record_history(job, title, "Error")

    def _record_history(self, job, title, status):
        self.history.append({
            "url": job["url"],
            "title": title,
            "quality": job["quality_label"],
            "status": status,
            "time": datetime.now().isoformat(timespec="seconds"),
        })
        save_history(self.history)

    # ------------------------- UI queue poller ---------------------------- #
    def _poll_ui_queue(self):
        try:
            while True:
                kind, job_id, text, payload = self.ui_queue.get_nowait()
                iid = self.queue_items.get(job_id)
                if kind == "progress":
                    if iid:
                        self.tree.set(iid, "status", text)
                    if payload is not None:
                        self.progress["value"] = payload
                    self._set_status(f"Downloading... {text}")
                elif kind == "status":
                    if iid:
                        self.tree.set(iid, "status", text)
                elif kind == "done":
                    if iid:
                        self.tree.set(iid, "title", payload)
                        self.tree.set(iid, "status", "Done")
                    self.progress["value"] = 0
                    self._set_status(f"Finished: {payload}")
                elif kind == "error":
                    if iid:
                        self.tree.set(iid, "status", "Error")
                    self.progress["value"] = 0
                    self._set_status(text)
        except queue.Empty:
            pass
        self.root.after(120, self._poll_ui_queue)


# --------------------------------------------------------------------------- #
def main():
    try:
        yt_dlp_module = ensure_yt_dlp()
    except RuntimeError as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Missing dependency", str(e))
        return

    root = tk.Tk()
    try:
        ttk.Style().theme_use("clam")
    except tk.TclError:
        pass
    VideoDownloaderApp(root, yt_dlp_module)
    root.mainloop()


if __name__ == "__main__":
    main()
