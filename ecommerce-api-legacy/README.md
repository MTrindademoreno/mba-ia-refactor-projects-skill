# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot.

Exemplos de requisições estão em `api.http`.

# Analise manual
HIGH — exclusão de usuário quebra a integridade dos dados
src/AppManager.js:131-136 remove o usuário, mas mantém matrículas e pagamentos associados; a própria resposta confirma isso.
Impacto arquitetural: cria registros órfãos e relatórios inconsistentes. A regra deveria preservar integridade por transação, chaves estrangeiras ou estratégia explícita de remoção.

MEDIUM — checkout não é transacional
src/AppManager.js:50-61 cria matrícula, pagamento e auditoria em operações separadas. Se uma falhar após outra ter sido concluída, o sistema fica parcialmente atualizado.
Impacto arquitetural: compromete consistência do domínio financeiro; o fluxo precisa de transação e tratamento de compensação.

MEDIUM — banco em memória é recriado a cada inicialização
src/AppManager.js:7 usa new sqlite3.Database(':memory:'); schema e dados são recriados em initDb().
Impacto arquitetural: dados de usuários, matrículas e pagamentos desaparecem após reiniciar a API, impedindo comportamento persistente e confiável.

LOW — configuração, cache e criptografia em um módulo genérico
src/utils.js mistura config, globalCache, logging e badCrypto.
Impacto arquitetural: reduz coesão e torna dependências menos claras; cada preocupação deveria ter um módulo próprio.

LOW — bootstrap da aplicação depende de ordem implícita
src/app.js:8-10 exige que initDb() aconteça antes de setupRoutes(), mas essa regra não é explicitada por uma composição estruturada ou testes.
Impacto arquitetural: mudanças no bootstrap podem iniciar rotas com infraestrutura incompleta; uma factory/app builder deixaria a inicialização previsível.

# Construção da Skill

Decisões de design

Estruturei o SKILL.md em 3 fases com um gate de aprovação obrigatório entre a auditoria e a execução.

O conhecimento da skill ficou separado em arquivos por responsabilidade: heurísticas de detecção, catálogo de anti patterns, template de relatório, guidelines de arquitetura alvo e playbook de transformação. O SKILL.md só orquestra, não carrega conhecimento de domínio. 

A skill vive em .claude/skills/refactor-arch/, seguindo a convenção padrão do Claude Code, com paths internos relativos. Isso importava porque o requisito era ela ser copiável entre projetos sem edição, então copiar a pasta pros outros dois projetos foi um cp -r direto.

Catálogo de anti patterns e por quê

O mínimo pedido eram 8 anti patterns. Cheguei a 20 (CS 001 a CS 020), cobrindo duplicação, acoplamento, segurança, error handling, testabilidade e estilo. Optei por um catálogo maior porque numa análise manual eu só enxergo o que salta aos olhos, o mesmo viés que tenho quando reviso um PR grande e comento só os pontos mais óbvios. Um catálogo amplo obriga o agente a checar sistematicamente o que eu, sozinho, deixaria passar.

Isso se confirmou na prática: nos 3 projetos, a auditoria automática encontrou os 16 problemas que eu já tinha documentado na análise manual, mais entre 6 e 9 achados extras por projeto, incluindo CRITICALs de segurança (SQL injection, credenciais hardcoded, hash de senha reversível) que não estavam na minha lista original.

Também incluí detecção de APIs deprecated de propósito. É o mesmo reflexo que ganhei em Android quando o compileSdk sobe e o lint acusa uso de algo obsoleto: quis que a skill enxergasse não só a estrutura do código, mas também o que está rodando com API que não deveria mais usar.

Como garantiu que a skill é agnóstica de tecnologia

Essa foi a parte que mais me testou. Comecei com exemplos de código reais nos arquivos de referência e só numa revisão percebi que 100% dos exemplos do refactoring playbook.md estavam em Python, apesar do SKILL.md instruir "adapte pra stack detectada". É o mesmo tipo de falha que já vi em biblioteca interna Android documentada como genérica, mas cujo único exemplo na documentação todo mundo acaba copiando ao pé da letra em vez de generalizar o princípio.

A correção não foi adicionar um segundo exemplo em outra linguagem, porque isso só trocaria o viés de uma stack por duas. Reescrevi cada padrão de transformação como sinal de detecção, invariante que precisa continuar verdadeiro depois do fix, e pseudocódigo neutro (function, end function, placeholders como <bind_placeholder>, sem sintaxe real de nenhuma linguagem). O agente passa a precisar identificar primeiro o mecanismo idiomático da stack detectada na Fase 1, e só então escrever o código.

A prova concreta veio de rodar a skill nos 3 projetos e comparar os relatórios. code smells project e task manager api são Python/Flask em estágios de organização diferentes, ecommerce api legacy é Node/Express. Foi esse terceiro que validou de fato: o relatório recomendou process.env, hashing com crypto.scryptSync, transação SQLite com BEGIN/COMMIT, sem nenhum resquício de Flask ou Python. Isso comprova a Fase 1 (detecção) e a Fase 2 (auditoria) nas duas stacks. A Fase 3 (execução do refactor) ainda não rodou em nenhum projeto, então esse pedaço continua sendo design validado, não comportamento comprovado.

Desafios encontrados

Viés de linguagem escondido atrás de um texto que dizia "isso é só ilustrativo". Só apareceu numa revisão deliberada, não no primeiro rascunho.

Confiar no relatório sem comparar achado a achado com a análise manual foi uma tentação real. Só ao montar a comparação (5/5, 5/5, 6/6) ficou claro que a cobertura era genuína.

# Resultados

Relatório completo: [`reports/audit-project-2-ecommerce-api-legacy.md`](../reports/audit-project-2-ecommerce-api-legacy.md).

Resumo por severidade: **CRITICAL: 3 | HIGH: 5 | MEDIUM: 4 | LOW: 5** (17 findings no total).

Os 5 problemas da análise manual foram todos confirmados pela auditoria (5/5), inclusive com a checagem de transação do checkout elevada de MEDIUM (na minha leitura manual) para HIGH pelo audit. Além deles, a Fase 2 encontrou 8 achados adicionais, incluindo os 3 CRITICAL que não constavam na revisão manual:

- Segredos hardcoded em `src/utils.js` (senha de banco e uma chave de gateway de pagamento com cara de produção).
- `badCrypto`: "hash" de senha reversível baseado em base64 repetido, não é um algoritmo criptográfico de fato.
- God Object: `AppManager` concentra conexão de banco, schema, rotas e regra de negócio das 3 rotas em uma única classe.

O relatório também confirmou explicitamente a ausência de SQL injection (todas as queries já usam `?` com array de parâmetros) e de APIs deprecated nas versões de `express`/`sqlite3` em uso, em vez de simplesmente não mencionar o tema.

A Fase 3 já rodou neste projeto: `AppManager`/`utils.js` foram removidos e o código foi dividido em `routes/ → controllers/ → services/ → repositories/ → models/`; segredos passaram a vir de `.env` via `src/config/`; `badCrypto` foi trocado por `crypto.scryptSync` com salt; o checkout ficou transacional (`BEGIN`/`COMMIT`/`ROLLBACK`); a exclusão de usuário agora faz cascade-delete de matrículas e pagamentos na mesma transação; e o error handling foi centralizado em `src/middleware/errorHandler.js`. **Um gap real permanece:** este ambiente não tem runtime Node.js instalado, então o boot check e os smoke tests de `api.http` descritos no relatório nunca foram executados de fato — só revisados estaticamente. Veja abaixo como rodar essa validação.

**Validação manual pós-refatoração (pendente de execução — requer Node.js instalado)**

Suba o servidor num terminal (o `.env` já existe no projeto, gerado pela Fase 3, não precisa criar nada):

```powershell
cd ecommerce-api-legacy
npm install
npm start
```

A aplicação sobe em `http://localhost:3000`; o banco SQLite em memória é recriado com o seed (`Leonan`/`leonan@fullcycle.com.br`, cursos `Clean Architecture` R$997 e `Docker` R$497, 1 matrícula/pagamento existentes) a cada boot.

Em outro terminal (PowerShell), rode os quatro casos do `api.http`:

```powershell
# Checkout aprovado (cartão começando com "4")
Invoke-RestMethod -Uri http://localhost:3000/api/checkout -Method Post -ContentType "application/json" -Body (@{ usr = "Guilherme"; eml = "gui@fullcycle.com.br"; pwd = "senhaforte"; c_id = 2; card = "4111222233334444" } | ConvertTo-Json)

# Checkout recusado (cartão não começa com "4")
try { Invoke-RestMethod -Uri http://localhost:3000/api/checkout -Method Post -ContentType "application/json" -Body (@{ usr = "Joao"; eml = "joao@teste.com"; pwd = "123"; c_id = 1; card = "5111222233334444" } | ConvertTo-Json) } catch { $_.Exception.Response.StatusCode.value__ }

# Relatório financeiro
Invoke-RestMethod http://localhost:3000/api/admin/financial-report

# Delete de usuário com cascade (matrículas/pagamentos)
Invoke-RestMethod -Uri http://localhost:3000/api/users/1 -Method Delete
```

**Executado em 2026-08-16, com Node.js v24.19.0 instalado via `winget install OpenJS.NodeJS.LTS`.** `npm install` (191 pacotes, sem erros de build do `sqlite3` nativo) seguido de `npm start` — boot confirmado pelo log `Frankenstein LMS rodando na porta 3000...`. Resultado real dos quatro casos de `api.http`, mais uma checagem extra do relatório após o delete:

```
POST /api/checkout (cartão "4...")   -> 200 {"msg":"Sucesso","enrollment_id":2}
POST /api/checkout (cartão "5...")   -> 400 "Pagamento recusado"
GET  /api/admin/financial-report      -> 200, Clean Architecture (997, Leonan) + Docker (497, Guilherme)
DELETE /api/users/1                   -> 200 "Usuário deletado com sucesso, incluindo matrículas e pagamentos associados."
GET  /api/admin/financial-report (pós-delete) -> 200, Clean Architecture zerado (revenue: 0, students: []); Docker inalterado (497, Guilherme)
```

Bateu exatamente com o previsto no relatório da Fase 3: o checkout aprovado/recusado, o relatório financeiro agregado, e o cascade-delete removendo especificamente a matrícula/pagamento do usuário 1 sem afetar o pagamento de outro usuário no mesmo curso — confirmando que a transação e o cascade-delete funcionam de fato, não só na leitura estática do código.

## Checklist de Validação

### Fase 1 — Análise
- [x] Linguagem detectada corretamente
- [x] Framework detectado corretamente
- [x] Domínio da aplicação descrito corretamente
- [x] Número de arquivos analisados condiz com a realidade

### Fase 2 — Auditoria
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados
- [x] Detecção de APIs deprecated incluída (se aplicável)
- [x] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [x] Estrutura de diretórios segue padrão MVC — `src/{config,db,models,repositories,services,controllers,routes,middleware,errors,utils}/`
- [x] Configuração extraída para módulo de config (sem hardcoded) — `src/config/index.js` lê de `process.env` (via `src/config/env.js`, `.env`/`.env.example`), sem segredos no código-fonte
- [x] Models criados para abstrair dados — `src/models/{User,Course,Enrollment}.js` mapeiam linhas do SQLite para objetos de domínio consumidos pelos repositories
- [x] Views/Routes separadas para visualização ou roteamento — `src/routes/index.js`
- [x] Controllers concentram o fluxo da aplicação — `src/controllers/*Controller.js`
- [x] Error handling centralizado — `src/errors/HttpError.js` + `src/middleware/errorHandler.js`
- [x] Entry point claro — `src/app.js` expõe `createApp()` (composition root) e só chama `app.listen` quando executado diretamente
- [x] Aplicação inicia sem erros — Node.js v24.19.0 instalado (`winget install OpenJS.NodeJS.LTS`); `npm install` + `npm start` sobem o servidor e logam `Frankenstein LMS rodando na porta 3000...` sem erro
- [x] Endpoints originais respondem corretamente — os 4 casos de `api.http` foram executados contra o servidor real: checkout aprovado (200), checkout recusado (400), relatório financeiro (200) e delete de usuário com cascade confirmado (relatório pós-delete mostra a matrícula/pagamento do usuário removidos, sem afetar outros usuários) — ver seção "Validação manual pós-refatoração" acima
