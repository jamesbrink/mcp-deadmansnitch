# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-01-16

### Breaking Changes
- **Consolidated 10 MCP tools into single unified `snitch` tool** with `action` parameter
  - Old: `list_snitches()`, `get_snitch()`, `create_snitch()`, etc.
  - New: `snitch(action="list")`, `snitch(action="get", token="...")`, etc.
  - This reduces context usage when connecting to LLMs

### Added
- Docker image support via Nix flake (`nix build .#docker`)
- Nix CI/CD job for flake validation and Docker builds
- FlakeHub publishing workflow for tagged releases
- FlakeHub and Nix flake badges in README
- Docker usage documentation in README and NIX.md
- OCI metadata labels on Docker image (version, revision, author, etc.)
- Clean server exit handling (no traceback on Ctrl+C)
- Beta release workflow for testing on TestPyPI before production
- RELEASING.md documentation for release process

### Changed
- Production releases now require TestPyPI success before PyPI
- Docker image timestamp uses git commit date instead of Unix epoch

### Fixed
- Server now exits cleanly on KeyboardInterrupt (Ctrl+C)
- Nix flake builds include lupa dependency

## [0.1.1] - 2025-01-26

### Fixed
- Fixed MCP tool parameter parsing issue with Claude Code by removing Pydantic models from tool decorators
- Tools now use direct function parameters instead of Pydantic models to avoid serialization issues
- This resolves the "Input validation error: '{}' is not of type 'object'" error when using MCP tools

### Changed
- Updated all test files to work with the new parameter structure
- Improved code formatting to comply with linting standards
- Clarified documentation for pause_snitch to indicate it only accepts ISO 8601 timestamps

### Added
- Test coverage for edge cases including array parameter handling, pause duration formats, and tag removal behavior
- Documentation clarifying proper array parameter syntax for MCP tools

## [0.1.0] - 2025-01-24

### Added
- Initial release of mcp-deadmansnitch
- MCP server implementation for Dead Man's Snitch monitoring service
- Support for all Dead Man's Snitch API operations:
  - List snitches with optional tag filtering
  - Get snitch details
  - Create new snitches
  - Update existing snitches
  - Delete snitches
  - Check in (ping) snitches
  - Pause/unpause snitches
  - Add/remove tags
- Comprehensive test suite with 73 tests
- Full documentation and examples
- Claude Desktop integration support