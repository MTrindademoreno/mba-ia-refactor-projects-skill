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