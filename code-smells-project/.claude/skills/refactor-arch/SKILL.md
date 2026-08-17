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
5. Only Phase 2 writes a report file to disk. Decide its single location before starting Phase 1, and never end up with copies in two places. Check whether a `reports/` directory already exists one level above the project root, containing files named `audit-project-<N>-*.md`. If so, this project is part of a multi-project submission sharing that convention: write the Phase 2 report there as `audit-project-<N>-<slug>.md` (reuse its existing `<N>` if present, otherwise pick the next unused one), and do not create a project-local `reports/` directory. If no such sibling directory/convention exists, store it under `<project-root>/reports/` as `<slug>-phase2-audit.md` instead, and never create one from scratch or invent project numbering. Use a concise slug derived from the project directory name for the filename. Phase 1 and Phase 3 never write a report file — see their sections below for where that content goes instead.

## Phases

### Phase 1 - Discover

Analyze the project without modifying application files.

- Read [analysis-heuristics.md](./analysis-heuristics.md) to identify the language, framework, runtime, package manager, persistence, entry points, tests, and deployment signals.
- Map modules, dependencies, boundaries, and the current architectural style from actual source and configuration files.
- Read [reference-templates.md](./reference-templates.md) and present the Phase 1 report directly in your response, using that template's structure. Do not write it to a file — Phase 1 has no report file, only Phase 2 does (see Establish Scope step 5).
- State evidence and uncertainties. Do not infer a framework, database, domain, or file count without inspecting it.
- Update the `## Checklist de Validação` section in the project's `README.md` (create it from the template in reference-templates.md if absent), checking off the Fase 1 items you verified with evidence.

### Phase 2 - Audit

Audit without modifying application files.

- Read [architecture-quality-standards.md](./architecture-quality-standards.md) and evaluate only findings supported by concrete evidence.
- For each finding, record severity, exact file and line range, evidence, impact, and a technology-appropriate recommendation. Order findings from CRITICAL to LOW.
- Check deprecated APIs against the project's installed versions and official documentation or local migration guidance when available; do not flag APIs as deprecated by guesswork.
- Read [reference-templates.md](./reference-templates.md) and produce the Phase 2 report as `<slug>-phase2-audit.md` (or `audit-project-<N>-<slug>.md` if the multi-project convention from Establish Scope step 5 applies), in that single location. Re-running Phase 2 updates that same file in place — never leave an older copy behind under a different name.
- Propose a minimal, incremental refactoring plan that preserves behavior and names the tests or checks that will validate each change.
- Update the `## Checklist de Validação` section in the project's `README.md`, checking off the Fase 2 items you verified with evidence.
- Stop after presenting the report and plan. Ask the user for explicit approval before entering Phase 3 or writing any application file.

### Phase 3 - Refactor and Validate

Run this phase only after the user explicitly approves the Phase 2 plan.

- Read [mvc-architecture-guidelines.md](./mvc-architecture-guidelines.md) for separation-of-concerns principles and choose a target layout compatible with the detected stack.
- Read [refactoring-playbook.md](./refactoring-playbook.md) only for transformations relevant to confirmed findings. Translate examples to the project's language and libraries instead of copying them mechanically.
- Implement the approved changes in small, behavior-preserving steps. Keep framework-required entry points, route contracts, configuration conventions, and migration requirements intact.
- Before treating Phase 3 as done, check the implementation against every item in the Fase 3 section of the Checklist de Validação template (reference-templates.md), including "Error handling centralizado". Never mark Phase 3 complete, nor the checklist checked off, while an item is unmet just because it fell outside the initial pass — go back and apply the smallest behavior-preserving change needed to satisfy it, as long as it stays within the approved Phase 2 scope. Only leave an item unchecked when satisfying it would require scope the user has not approved (e.g., a breaking contract change) or the item does not apply to the detected stack — in that case say so explicitly next to the item instead of leaving it silently unchecked.
- Treat this as a loop, not a single pass: every time you make a change in Phase 3 (including a change applied specifically to close a checklist gap), immediately re-evaluate whichever checklist item(s) that change affects and update their checkbox in the project's `README.md` to match the new state — check it off the moment it is genuinely satisfied, uncheck it if a later change regresses it. Do not defer every checkbox update to a single pass at the end of the phase.
- Run the project's existing formatter, static checks, tests, build, boot check, and endpoint smoke tests where available. If a check cannot run, explain why and state the remaining validation risk.
- Present the Phase 3 report directly in your response, using the Phase 3 template's structure (changes, validation commands and results, unresolved findings, follow-up work). Do not write it to a file — Phase 3 has no report file, only Phase 2 does (see Establish Scope step 5). Its permanent record is the project's own `README.md`, via the next bullet.
- Before finishing, do a final sweep of the `## Checklist de Validação` section in the project's `README.md` to confirm every Fase 3 checkbox still reflects the current code, and update the "Resultados"-style narrative there with what changed and how it was validated, noting the reason next to any item you leave unchecked. This is the durable record of Phase 3 — there is no separate report file for it.

## Report Quality

- Use the templates as a structure, not as a substitute for evidence.
- Count only inspected source files and clearly label estimates.
- Prefer a smaller number of high-confidence findings over speculative findings.
- Treat every report as project-specific output; never reuse example-project names, paths, modules, or findings.

## Copying the Package

This directory is the canonical source. To run the skill in another project, copy this entire directory into the target repository as `.claude/skills/refactor-arch/`, keeping `SKILL.md` and its five Markdown references together and unmodified. Relative links are intentionally local, so no repository-specific absolute path or project name needs to be edited after copying. Once a target project has its own copy, invoke it there with `/refactor-arch`; do not keep long-lived duplicate copies inside this repository beyond the run that needs them.
