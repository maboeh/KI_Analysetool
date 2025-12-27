## Sentinel's Journal

## 2024-05-22 - [SSRF Risk in Website Analysis]
**Vulnerability:** Server-Side Request Forgery (SSRF) risk in `extract_text_from_website` function.
**Learning:** The application accepts a URL from the user and directly passes it to `requests.get()` without any validation or filtering. This could allow an attacker to make the server send requests to internal network resources (e.g., `http://localhost`, `http://192.168.x.x`) or other sensitive endpoints, potentially exposing internal services or metadata services (like AWS instance metadata).
**Prevention:** Implement strict URL validation. Allow only specific schemes (http, https). Block private/local IP ranges (localhost, 127.0.0.1, 10.x.x.x, 192.168.x.x, etc.). Ideally, use a dedicated library or robust regex for IP checking if domain resolution is involved, but at least blocking common local addresses is a good first step.
