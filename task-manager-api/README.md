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
