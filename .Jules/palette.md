## 2024-05-23 - Threading in Tkinter
**Learning:** Tkinter UI updates must happen on the main thread. When introducing threading for long-running tasks (like AI analysis), use `root.after(0, callback)` to schedule UI updates from the background thread.
**Action:** Always wrap UI updates in a callback scheduled on the main loop when working with threads in Tkinter.
## 2024-10-24 - Async Loading States
**Learning:** Users perceive the application as "crashed" when synchronous long-running operations block the UI without visual feedback. Tkinter requires explicit `update()` calls or threading to update the UI during these operations.
**Action:** Always implement a visual loading indicator (cursor change, status bar update) and disable trigger buttons before starting any potentially long-running operation, even if using the main thread.
