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
6. Check whether a `reports/` directory already exists one level above the project root, containing files named `audit-project-<N>-*.md`. If so, this project is part of a multi-project submission sharing that convention: keep that sibling folder in sync (see Phase 2). If no such sibling directory/convention exists, ignore this entirely — never create one from scratch or invent project numbering.

## Phases

### Phase 1 - Discover

Analyze the project without modifying application files.

- Read [analysis-heuristics.md](./analysis-heuristics.md) to identify the language, framework, runtime, package manager, persistence, entry points, tests, and deployment signals.
- Map modules, dependencies, boundaries, and the current architectural style from actual source and configuration files.
- Read [reference-templates.md](./reference-templates.md) and produce the Phase 1 report as `<slug>-phase1-analysis.md`.
- State evidence and uncertainties. Do not infer a framework, database, domain, or file count without inspecting it.
- Update the `## Checklist de Validação` section in the project's `README.md` (create it from the template in reference-templates.md if absent), checking off the Fase 1 items you verified with evidence.

### Phase 2 - Audit

Audit without modifying application files.

- Read [architecture-quality-standards.md](./architecture-quality-standards.md) and evaluate only findings supported by concrete evidence.
- For each finding, record severity, exact file and line range, evidence, impact, and a technology-appropriate recommendation. Order findings from CRITICAL to LOW.
- Check deprecated APIs against the project's installed versions and official documentation or local migration guidance when available; do not flag APIs as deprecated by guesswork.
- Read [reference-templates.md](./reference-templates.md) and produce `<slug>-phase2-audit.md`.
- Propose a minimal, incremental refactoring plan that preserves behavior and names the tests or checks that will validate each change.
- Update the `## Checklist de Validação` section in the project's `README.md`, checking off the Fase 2 items you verified with evidence.
- If the sibling-submission convention from Establish Scope step 6 applies, also write this same Phase 2 audit content (verbatim) to the sibling file: reuse its existing number `<N>` if `audit-project-<N>-<slug>.md` already exists there, otherwise pick the next unused `<N>`. This sibling file always mirrors the current `<slug>-phase2-audit.md` exactly — re-running Phase 2 must update it too, not just the project-local copy.
- Stop after presenting the report and plan. Ask the user for explicit approval before entering Phase 3 or writing any application file.

### Phase 3 - Refactor and Validate

Run this phase only after the user explicitly approves the Phase 2 plan.

- Read [mvc-architecture-guidelines.md](./mvc-architecture-guidelines.md) for separation-of-concerns principles and choose a target layout compatible with the detected stack.
- Read [refactoring-playbook.md](./refactoring-playbook.md) only for transformations relevant to confirmed findings. Translate examples to the project's language and libraries instead of copying them mechanically.
- Implement the approved changes in small, behavior-preserving steps. Keep framework-required entry points, route contracts, configuration conventions, and migration requirements intact.
- Before treating Phase 3 as done, check the implementation against every item in the Fase 3 section of the Checklist de Validação template (reference-templates.md), including "Error handling centralizado". Never mark Phase 3 complete, nor the checklist checked off, while an item is unmet just because it fell outside the initial pass — go back and apply the smallest behavior-preserving change needed to satisfy it, as long as it stays within the approved Phase 2 scope. Only leave an item unchecked when satisfying it would require scope the user has not approved (e.g., a breaking contract change) or the item does not apply to the detected stack — in that case say so explicitly next to the item instead of leaving it silently unchecked.
- Treat this as a loop, not a single pass: every time you make a change in Phase 3 (including a change applied specifically to close a checklist gap), immediately re-evaluate whichever checklist item(s) that change affects and update their checkbox in the project's `README.md` to match the new state — check it off the moment it is genuinely satisfied, uncheck it if a later change regresses it. Do not defer every checkbox update to a single pass at the end of the phase.
- Run the project's existing formatter, static checks, tests, build, boot check, and endpoint smoke tests where available. If a check cannot run, explain why and state the remaining validation risk.
- Produce `<slug>-phase3-refactoring.md` using the Phase 3 template, including changes, validation commands and results, unresolved findings, and follow-up work, under the project-local `reports/` directory only.
- Before writing the report, do a final sweep of the `## Checklist de Validação` section in the project's `README.md` to confirm every Fase 3 checkbox still reflects the current code, then note any remaining unchecked item's reason in the phase 3 report too. This is the only Phase 3 update that belongs in the README.
- Do not create or write to the sibling submission `reports/` directory from Establish Scope step 6. That convention exists only for the Phase 2 audit file; Phase 3 never has a sibling counterpart there.

## Report Quality

- Use the templates as a structure, not as a substitute for evidence.
- Count only inspected source files and clearly label estimates.
- Prefer a smaller number of high-confidence findings over speculative findings.
- Treat every report as project-specific output; never reuse example-project names, paths, modules, or findings.

## Copying the Package

This directory is the canonical source. To run the skill in another project, copy this entire directory into the target repository as `.claude/skills/refactor-arch/`, keeping `SKILL.md` and its five Markdown references together and unmodified. Relative links are intentionally local, so no repository-specific absolute path or project name needs to be edited after copying. Once a target project has its own copy, invoke it there with `/refactor-arch`; do not keep long-lived duplicate copies inside this repository beyond the run that needs them.
