## 2024-10-24 - Async Loading States
**Learning:** Users perceive the application as "crashed" when synchronous long-running operations block the UI without visual feedback. Tkinter requires explicit `update()` calls or threading to update the UI during these operations.
**Action:** Always implement a visual loading indicator (cursor change, status bar update) and disable trigger buttons before starting any potentially long-running operation, even if using the main thread.
