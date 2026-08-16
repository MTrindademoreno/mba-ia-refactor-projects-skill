# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo.


# Analise manual
HIGH — módulo models.py concentra múltiplos domínios e responsabilidades
models.py reúne persistência e regras de produtos, usuários, autenticação, pedidos, estoque, relatórios e buscas.
Impacto arquitetural: o módulo tem muitos motivos para mudar, dificulta testes isolados e impede evolução independente por domínio.

MEDIUM — regras de validação duplicadas nos controllers
criar_produto e atualizar_produto em controllers.py repetem validações de nome, preço e estoque.
Impacto arquitetural: regras de negócio ficam acopladas à camada HTTP e tendem a divergir com o tempo.

MEDIUM — acesso a dados ineficiente e misturado à montagem de resposta
get_pedidos_usuario e get_todos_pedidos em models.py fazem consultas adicionais dentro de loops.
Impacto arquitetural: a camada de persistência não encapsula uma estratégia eficiente de carregamento; o desempenho degrada conforme o sistema cresce.

LOW — regras de domínio hardcoded nos controllers
Categorias de produto (controllers.py:52) e status de pedido (controllers.py:242) estão definidos diretamente nas funções HTTP.
Impacto arquitetural: mudanças no domínio exigem editar controllers, quando deveriam ficar em constantes, enumerações ou uma camada de negócio.

LOW — contratos entre camadas são implícitos
Funções em controllers.py e models.py não possuem tipos, objetos de entrada/saída ou contratos documentados.
Impacto arquitetural: aumenta o acoplamento implícito e torna refatorações mais arriscadas, pois não está claro quais dados cada camada deve receber ou retornar.

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

Relatório completo: [`reports/audit-project-1-code-smells-project.md`](../reports/audit-project-1-code-smells-project.md).

Resumo por severidade: **CRITICAL: 4 | HIGH: 4 | MEDIUM: 3 | LOW: 3** (14 findings no total).

Os 5 problemas da análise manual foram todos confirmados pela auditoria (5/5). Além deles, a Fase 2 encontrou 9 achados adicionais, incluindo os 4 CRITICAL que não constavam na revisão manual:

- SQL injection generalizada em `models.py`, em praticamente toda função que monta query por concatenação de string.
- `/admin/query`: endpoint sem autenticação que executa SQL arbitrário vindo do corpo da requisição.
- `/admin/reset-db`: endpoint destrutivo (apaga todas as tabelas) sem autenticação.
- `SECRET_KEY` hardcoded e devolvido no corpo da resposta de `/health`, junto com o flag de debug.

A Fase 3 já rodou neste projeto (relatório completo em [`reports/code-smells-project-phase3-refactoring.md`](reports/code-smells-project-phase3-refactoring.md)): `models.py` foi separado em `models/produtos.py`, `models/usuarios.py` e `models/pedidos.py`; `SECRET_KEY`/`DEBUG`/`DATABASE_PATH` passaram a vir de variável de ambiente via `config.py`; senhas agora são hasheadas com `werkzeug.security`; `/admin/reset-db` e `/admin/query` foram removidos; e todas as queries passaram a usar parâmetros vinculados.

**Validação manual pós-refatoração**

Suba o servidor num terminal:

```powershell
cd code-smells-project
pip install -r requirements.txt
python app.py
```

Em outro terminal (PowerShell), rode:

```powershell
Invoke-RestMethod http://localhost:5000/health
Invoke-RestMethod http://localhost:5000/produtos
Invoke-RestMethod http://localhost:5000/usuarios

Invoke-RestMethod -Uri http://localhost:5000/login -Method Post -ContentType "application/json" -Body (@{ email = "admin@loja.com"; senha = "admin123" } | ConvertTo-Json)
```

Resultado esperado:

```
GET /health    -> database: connected | db_path: loja.db | status: ok | versao: 1.0.0
GET /produtos  -> 4 produtos retornados, sucesso: True
GET /usuarios  -> 3 usuários retornados (id, nome, email, tipo, criado_em), sem o campo "senha", sucesso: True
POST /login    -> {email: admin@loja.com, senha: admin123} -> mensagem: "Login OK", sucesso: True
```

Confirma na prática dois dos achados CRITICAL corrigidos: a senha não é mais exposta pela API (`GET /usuarios`) e o login funciona corretamente contra a senha já hasheada no seed, sem regressão de comportamento.

