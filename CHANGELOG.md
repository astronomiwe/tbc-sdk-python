# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-10-02

### Added

- Callback parsing through `parse_callback` and `TBCCallbackError`.
- Optional FastAPI and Django callback adapters with runnable examples.
- A weekly TBC sandbox contract workflow, enabled only when its credentials are configured.
- MkDocs guides for payment lifecycle, callbacks, framework integration, advanced payments,
  sandbox operations, and the public API.

### Changed

- Validate payment and recurring IDs, callback URLs, merchant payment IDs, and paired
  split-payment correlation fields before sending an API request.

## [0.2.0] - 2026-10-02

### Added

- `TBCResponseError` for successful API responses that do not match the documented schema.

### Changed

- Validate access-token, payment, completion, recurring-card, and payment-link response data.

## [0.1.0] - 2026-10-01

### Added

- Typed synchronous and asynchronous clients for TBC Checkout.
- Payment creation, lookup, cancellation, pre-authorization completion, recurring
  payments, and installment requests.
- Sandbox support, structured API errors, token management, and conservative retries.
