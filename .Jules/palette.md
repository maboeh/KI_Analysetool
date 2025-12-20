## 2024-05-23 - Threading in Tkinter
**Learning:** Tkinter UI updates must happen on the main thread. When introducing threading for long-running tasks (like AI analysis), use `root.after(0, callback)` to schedule UI updates from the background thread.
**Action:** Always wrap UI updates in a callback scheduled on the main loop when working with threads in Tkinter.
