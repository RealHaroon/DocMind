# Repository Guidelines

## Project Overview

DocMind is currently an early-stage project. Keep changes small, focused, and easy to review. Do not assume a language, framework, package manager, or deployment target until the repository establishes one.

## Repository Structure

- `README.md` contains the project overview and setup instructions.
- `LICENSE` contains the Apache License 2.0 terms.
- Add source code, tests, documentation, and configuration in conventional locations for the chosen technology stack.
- Keep generated files, dependency caches, build outputs, secrets, and local environment files out of version control.

## Development Workflow

- Read the relevant files before making changes.
- Preserve existing user changes and avoid unrelated rewrites.
- Prefer the smallest implementation that fully addresses the task.
- Update documentation when behavior, setup, commands, or architecture changes.
- Add or update tests for behavior changes when a test framework exists.
- Run the narrowest relevant checks first, then broader checks when practical.

## Code Quality

- Follow established project conventions once they exist.
- Use clear names and keep functions and modules focused.
- Handle errors explicitly and provide actionable messages.
- Avoid unnecessary dependencies and abstractions.
- Never commit credentials, tokens, private keys, or sensitive document contents.

## Commits and Reviews

- Use concise, imperative commit messages.
- Keep commits logically scoped.
- In change summaries, state what changed, why, and how it was verified.
- Call out unverified behavior, known limitations, migrations, or follow-up work.

## Safety

- Do not delete or overwrite user data unless explicitly requested.
- Treat uploaded documents and extracted content as potentially sensitive.
- Validate untrusted input and avoid logging sensitive data.
- Ask before introducing irreversible migrations or materially changing public interfaces.
