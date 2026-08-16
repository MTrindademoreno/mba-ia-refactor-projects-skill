---
name: refactor-arch
description: "Analyze and refactor a software project in three phases: discover the stack and current architecture, audit code smells and risks, then only after explicit approval apply and validate an architecture improvement. Use for any application repository when a structured architecture assessment, audit report, or safe refactoring plan is needed."
---

# Architecture Refactoring Workflow

Execute the phases in order unless the user explicitly asks for one phase only. Adapt the target architecture to the application's style and framework; do not force MVC terminology or a directory layout when it would conflict with the framework's conventions.

## Establish Scope

1. Treat the current workspace as the project root, unless the user supplies a different path.
2. Identify the repository root from version-control and build manifests when possible.
3. Exclude generated, vendor, dependency, cache, build, coverage, and skill-package directories from source analysis. Never inspect or modify the copied skill as application source.
4. Preserve existing user changes. Do not delete, rename, overwrite, migrate data, expose secrets, or change public contracts without explicit approval.
5. Store reports under `<project-root>/reports/` unless the user requests another location. Use a concise slug derived from the project directory name for report filenames.

## Phases

### Phase 1 - Discover

Analyze the project without modifying application files.

- Read [analysis-heuristics.md](./analysis-heuristics.md) to identify the language, framework, runtime, package manager, persistence, entry points, tests, and deployment signals.
- Map modules, dependencies, boundaries, and the current architectural style from actual source and configuration files.
- Read [reference-templates.md](./reference-templates.md) and produce the Phase 1 report as `<slug>-phase1-analysis.md`.
- State evidence and uncertainties. Do not infer a framework, database, domain, or file count without inspecting it.

### Phase 2 - Audit

Audit without modifying application files.

- Read [architecture-quality-standards.md](./architecture-quality-standards.md) and evaluate only findings supported by concrete evidence.
- For each finding, record severity, exact file and line range, evidence, impact, and a technology-appropriate recommendation. Order findings from CRITICAL to LOW.
- Check deprecated APIs against the project's installed versions and official documentation or local migration guidance when available; do not flag APIs as deprecated by guesswork.
- Read [reference-templates.md](./reference-templates.md) and produce `<slug>-phase2-audit.md`.
- Propose a minimal, incremental refactoring plan that preserves behavior and names the tests or checks that will validate each change.
- Stop after presenting the report and plan. Ask the user for explicit approval before entering Phase 3 or writing any application file.

### Phase 3 - Refactor and Validate

Run this phase only after the user explicitly approves the Phase 2 plan.

- Read [mvc-architecture-guidelines.md](./mvc-architecture-guidelines.md) for separation-of-concerns principles and choose a target layout compatible with the detected stack.
- Read [refactoring-playbook.md](./refactoring-playbook.md) only for transformations relevant to confirmed findings. Translate examples to the project's language and libraries instead of copying them mechanically.
- Implement the approved changes in small, behavior-preserving steps. Keep framework-required entry points, route contracts, configuration conventions, and migration requirements intact.
- Run the project's existing formatter, static checks, tests, build, boot check, and endpoint smoke tests where available. If a check cannot run, explain why and state the remaining validation risk.
- Produce `<slug>-phase3-refactoring.md` using the Phase 3 template, including changes, validation commands and results, unresolved findings, and follow-up work.

## Report Quality

- Use the templates as a structure, not as a substitute for evidence.
- Count only inspected source files and clearly label estimates.
- Prefer a smaller number of high-confidence findings over speculative findings.
- Treat every report as project-specific output; never reuse example-project names, paths, modules, or findings.

## Copying the Package

This directory is the canonical source. To run the skill in another project, copy this entire directory into the target repository as `.claude/skills/refactor-arch/`, keeping `SKILL.md` and its five Markdown references together and unmodified. Relative links are intentionally local, so no repository-specific absolute path or project name needs to be edited after copying. Once a target project has its own copy, invoke it there with `/refactor-arch`; do not keep long-lived duplicate copies inside this repository beyond the run that needs them.
