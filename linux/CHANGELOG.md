# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Automated CI/CD pipeline with GitHub Actions
- Support for Linux installation via CURL
- Support for Linux installation via APT repository
- Docker container support via GHCR
- Codecov integration for test coverage
- Security improvements with bcrypt password hashing
- SSL certificate verification enabled
- SQL injection protection
- Secure cookie configuration

### Changed
- Migrated from SHA-256 to bcrypt for password hashing
- Enabled SSL verification for HTTP requests
- Improved error handling and logging
- Added input validation with Pydantic

## [1.0.0] - 2024-02-17

### Added
- Initial release
- Website uptime monitoring
- SSL certificate expiration tracking
- Multi-channel notifications (Telegram, Email, Slack, Discord, Teams, SMS)
- Web-based dashboard
- REST API
- User authentication with bcrypt
- Session management
- Status history tracking
- Cross-platform support (Windows, Linux)

### Security
- bcrypt password hashing
- SQL injection protection
- Secure cookie configuration
- SSL verification enabled

[Unreleased]: https://github.com/ajjs1ajjs/Uptime-Monitor-APP/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/ajjs1ajjs/Uptime-Monitor-APP/releases/tag/v1.0.0
