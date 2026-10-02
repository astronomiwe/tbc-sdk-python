# Sandbox and operations

Pass `sandbox=True` to use `https://test-api.tbcbank.ge/v1`.

```python
TBCClient("api-key", "client-id", "client-secret", sandbox=True)
```

The repository includes a weekly sandbox contract workflow. Configure these GitHub
Actions secrets to enable it:

- `TBC_SANDBOX_API_KEY`
- `TBC_SANDBOX_CLIENT_ID`
- `TBC_SANDBOX_CLIENT_SECRET`
- `TBC_SANDBOX_RETURN_URL`

The check creates a low-value sandbox payment and fetches it by ID. It does not
complete or cancel payments. Without all four secrets, the workflow reports that it
was skipped and makes no TBC request.

Keep API keys and client secrets out of source control, logs, browser code, and error
reports. See `SECURITY.md` for vulnerability reporting guidance.
