## 2024-12-22 - [Synchronous Operations Freeze UI]
**Learning:** Performing network requests (YouTube/Web extraction, OpenAI API) in the Tkinter main thread causes the entire application to freeze, leading to a "broken" user experience.
**Action:** Use `threading.Thread` for long-running tasks and `window.after` to schedule UI updates on the main thread. Always provide immediate feedback (cursor change, status message) before starting background work.
