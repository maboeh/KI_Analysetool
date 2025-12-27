## 2024-05-23 - [Input Validation and Timeout]
**Vulnerability:** Missing URL validation and timeout in network requests.
**Learning:** Network requests to arbitrary URLs without validation can lead to SSRF or unexpected behavior. Lack of timeouts can cause DoS.
**Prevention:** Validate URL schemes and enforce timeouts on all network operations.
