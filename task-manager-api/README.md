# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Diferente dos outros projetos, este já possui alguma separação de camadas (`models/`, `routes/`, `services/`, `utils/`), mas ainda contém problemas arquiteturais e de qualidade.

## Como rodar

```bash
pip install -r requirements.txt
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` popula o banco SQLite (`tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias.

# Analise manual
CRITICAL — segredos hardcoded e hashing de senha fraco expõem dados sensíveis
app.py:13 fixa o SECRET_KEY do Flask no código, services/notification_service.py:9-10 fixa usuário e senha do SMTP, e models/user.py:27-32 usa MD5 sem salt para senhas, cujo hash ainda é devolvido em toda resposta de usuário por to_dict() (models/user.py:16-25).
Impacto arquitetural: segredos versionados no repositório sem variável de ambiente ou cofre; senhas usam um algoritmo criptograficamente quebrado e o próprio hash é exposto pela API em create_user, update_user, get_user, get_users e login — combinação que facilita comprometer contas reais.

HIGH — endpoints não verificam autenticação; o token de login nunca é validado
routes/user_routes.py:207-211 gera um token fixo ('fake-jwt-token-' + id) no login, mas nenhuma rota em task_routes.py, user_routes.py ou report_routes.py exige esse token, um header de autorização, ou usa User.is_admin() para restringir acesso.
Impacto arquitetural: qualquer cliente lê, cria, altera e apaga tasks, usuários e relatórios sem se autenticar; o modelo de papéis (admin/manager/user) já existe no domínio, mas nunca protege uma rota.

MEDIUM — consultas N+1 ao montar respostas de tasks e relatórios
routes/task_routes.py:41-57 busca User e Category em uma query própria por task dentro do loop de get_tasks, e routes/report_routes.py:53-68 faz uma query de tasks por usuário dentro do loop de summary_report.
Impacto arquitetural: o número de queries cresce linearmente com o volume de dados mesmo havendo relationship() já mapeado em Task (user, category), degradando a performance conforme o sistema cresce.

MEDIUM — regra de negócio "overdue" duplicada em cinco lugares diferentes
models/task.py:50-60 define is_overdue(), mas a mesma verificação é reescrita manualmente em routes/task_routes.py:30-39 e :71-80, routes/user_routes.py:171-180, e routes/report_routes.py:33-37 e :132-135.
Impacto arquitetural: qualquer ajuste na regra de atraso (ex.: tolerância de dias, exceções por status) precisa ser replicado em todos esses pontos, criando alto risco de divergência entre endpoints.

LOW — serialização de Task remontada manualmente em vez de reaproveitar to_dict()
routes/task_routes.py:16-59 (get_tasks) e routes/user_routes.py:161-181 (get_user_tasks) reconstroem campo a campo o mesmo dicionário que Task.to_dict() (models/task.py:23-36) já produz, com pequenas divergências de formato entre os endpoints.
Impacto arquitetural: cada endpoint mantém sua própria cópia da serialização; adicionar ou renomear um campo do model exige lembrar de atualizar cada rota manualmente, e já existem inconsistências entre elas.

LOW — imports não utilizados nos módulos
routes/task_routes.py:7 importa json, os, sys e time sem uso; routes/user_routes.py:6 importa hashlib e json sem uso (o hashing de senha vive em User); utils/helpers.py:3-7 importa os, json, sys, math e hashlib sem uso.
Impacto arquitetural: imports não utilizados dificultam identificar as dependências reais de cada módulo e sinalizam falta de limpeza incremental do código.


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

Relatório completo: [`reports/audit-project-3-task-manager-api.md`](../reports/audit-project-3-task-manager-api.md).

Resumo por severidade: **CRITICAL: 2 | HIGH: 4 | MEDIUM: 3 | LOW: 2** (11 findings no total).

Os 6 problemas da análise manual foram todos confirmados pela auditoria (6/6); o achado único de segredos hardcoded + MD5 que eu tinha registrado como um item só foi desdobrado em dois findings CRITICAL separados pela Fase 2. Além deles, a Fase 2 encontrou 5 achados adicionais:

- `debug=True` com `host='0.0.0.0'`, expondo stack traces e o debugger interativo do Flask numa API que já não tem autenticação.
- Sete blocos `except:` genéricos que engolem o erro real em operações de escrita, sem log.
- Nenhuma camada de service/repository entre as rotas e o ORM, apesar de `services/` e `utils/` já existirem no projeto.
- `NotificationService` e a maior parte de `utils/helpers.py` são código morto, nunca importados fora do próprio arquivo.

Esse foi o único dos 3 projetos com organização parcial em camadas já existente (`models/`, `routes/`, `services/`, `utils/`), e mesmo assim a auditoria não deixou de encontrar praticamente os mesmos tipos de problema dos outros dois — o que reforça que estrutura de pastas sozinha não garante separação de responsabilidades real.

Fase 3 (execução do refactor) ainda não rodou neste projeto, então não há comparação de estrutura antes/depois nem validação de boot/endpoints pós-refatoração até o momento.