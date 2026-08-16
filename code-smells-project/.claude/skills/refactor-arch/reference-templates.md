# Report Templates

Use these templates for project-specific reports. Replace every placeholder with inspected evidence; omit sections that do not apply. Keep report filenames and phases consistent with `SKILL.md`.

## Phase 1 — Discovery

```markdown
================================
PHASE 1: PROJECT ANALYSIS
================================
Project:       <project name>
Language(s):   <detected languages>
Framework(s):  <framework and version, or none detected>
Runtime:       <runtime and package manager>
Dependencies:  <key production dependencies>
Domain:        <observed purpose, or unknown>
Architecture:  <current style and brief evidence>
Source files:  <inspected count>
Persistence:   <database, external storage, or none detected>
================================
```

Follow the block with:

- **Evidence:** entry points, manifests, configuration, tests, and primary modules inspected.
- **Architecture map:** module or layer, responsibility, and notable dependencies.
- **Constraints and uncertainties:** facts that need confirmation before a refactor.

## Phase 2 — Audit and Plan

```markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project:  <project name>
Stack:    <language, runtime, framework>
Files:    <inspected source files> | <lines, if measured>

Summary
CRITICAL: <N> | HIGH: <N> | MEDIUM: <N> | LOW: <N>
================================

## Findings

### [<SEVERITY>] <ID>: <short finding name>
File: <relative path>:<start line>-<end line>
Evidence: <what the source does>
Impact: <concrete risk or maintenance cost>
Recommendation: <smallest suitable change>

## Approved-scope proposal
1. <behavior-preserving change>
2. <behavior-preserving change>

## Validation plan
- <existing test, build, boot, or endpoint check>

Approval required: Do you approve this plan for Phase 3?
```

Add one subsection for every finding. Sort findings by severity, then by impact. Use a specific catalog ID when the issue matches the catalog; otherwise use a clear descriptive ID. Do not claim line ranges, versions, deprecations, or validation outcomes without evidence.

## Phase 3 — Refactoring and Validation

```markdown
================================
PHASE 3: REFACTORING COMPLETE
================================
Target architecture: <stack-appropriate style>

## Changed structure
<only directories and files actually added, moved, or materially changed>

## Changes made
- <finding ID>: <behavior-preserving change>

## Validation
| Check | Command or method | Result |
| --- | --- | --- |
| <test/build/boot/smoke check> | `<command>` | pass / fail / not run: <reason> |

## Remaining risks and follow-up
- <unresolved finding, migration requirement, or none>
================================
```

Show the project’s real paths and extensions. Do not prescribe a Python, Node, MVC, microservice, or layered directory tree unless it is compatible with the detected framework and approved plan.

## Validation Checklist (maintained in the project's README.md)

Every project's own `README.md` must contain this exact checklist, under a `## Checklist de Validação` heading. Create the section on the first phase that runs if it is not already present; on later phases, edit the existing section in place rather than appending a duplicate. Mark `[x]` only for an item you have concrete evidence for from the current run; leave `[ ]` for anything not yet reached, not run, or not verifiable, and add a short trailing note on that line explaining why (e.g. `- [ ] Fase 3 ainda não executada`). Never check an item by default or by inference.

```markdown
## Checklist de Validação

### Fase 1 — Análise
- [ ] Linguagem detectada corretamente
- [ ] Framework detectado corretamente
- [ ] Domínio da aplicação descrito corretamente
- [ ] Número de arquivos analisados condiz com a realidade

### Fase 2 — Auditoria
- [ ] Relatório segue o template definido nos arquivos de referência
- [ ] Cada finding tem arquivo e linhas exatos
- [ ] Findings ordenados por severidade (CRITICAL → LOW)
- [ ] Mínimo de 5 findings identificados
- [ ] Detecção de APIs deprecated incluída (se aplicável)
- [ ] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [ ] Estrutura de diretórios segue padrão MVC
- [ ] Configuração extraída para módulo de config (sem hardcoded)
- [ ] Models criados para abstrair dados
- [ ] Views/Routes separadas para visualização ou roteamento
- [ ] Controllers concentram o fluxo da aplicação
- [ ] Error handling centralizado
- [ ] Entry point claro
- [ ] Aplicação inicia sem erros
- [ ] Endpoints originais respondem corretamente
```
