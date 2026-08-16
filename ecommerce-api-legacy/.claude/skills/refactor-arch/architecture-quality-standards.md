# Architecture Quality Standards - Code Defects Reference

Referência de padrões de defeitos e violações arquiteturais baseado em princípios universais de qualidade de código, aplicáveis a qualquer linguagem de programação e framework. Focado em violações de MVC e SOLID.

## Definição de Severidades

Para padronizar auditorias e relatórios gerados pela IA, utilize a seguinte escala de classificação:

- **CRITICAL:** Falhas graves de arquitetura ou segurança que impedem o funcionamento correto, expõem dados sensíveis (ex: credenciais hardcoded, SQL Injection) ou violam completamente a separação de responsabilidades (ex: "God Class" contendo banco de dados, lógicas complexas e roteamento no mesmo arquivo).
- **HIGH:** Fortes violações do padrão MVC ou princípios SOLID que dificultam muito a manutenção e testes (ex: lógicas de negócio pesadas presas dentro de Controllers, forte acoplamento sem Injeção de Dependência, ou uso de estado global mutável em toda a aplicação).
- **MEDIUM:** Problemas de padronização, duplicação de código ou gargalos de performance moderada (ex: Queries N+1 no banco de dados, uso inadequado de middlewares, validações ausentes nas rotas).
- **LOW:** Melhorias de legibilidade, nomenclatura de variáveis ruins, ou "magic numbers" soltos pelo código.

---

## Categoria: DESIGN & ARCHITECTURE

### CS-001: Duplicated Code
**Severidade:** MEDIUM  
**Tipo:** Design  
**Descrição:**  
Código idêntico ou muito similar repetido em múltiplos lugares, violando o princípio DRY (Don't Repeat Yourself).

**Padrão Detectável:**
- Funções/métodos com lógica idêntica
- Validações repetidas
- Transformações de dados duplicadas
- Blocos de código copiados-colados

**Impacto:**
- Dificuldade em manutenção (mudanças replicadas)
- Risco de inconsistência
- Código mais longo e complexo

**Refatoração:**
- Extrair para função/método reutilizável
- Usar composição ou herança
- Aplicar strategy pattern

---

### CS-002: God Object (Large Class)
**Severidade:** HIGH  
**Tipo:** Design  
**Descrição:**  
Uma classe/módulo que faz demasiado e tem muitas responsabilidades, violando Single Responsibility Principle e padrão MVC.

**Padrão Detectável:**
- Classe/arquivo > 300-500 linhas
- Múltiplas razões para mudança
- Muitos métodos/funções públicos
- Baixa coesão entre membros
- Controller/Model contendo lógica de múltiplas responsabilidades

**Impacto:**
- Difícil de entender
- Difícil de testar
- Difícil de reutilizar
- Alto acoplamento com dependências
- Violação de SRP (Single Responsibility Principle)

**Refatoração:**
- Dividir em classes/módulos especializados
- Aplicar Strategy ou Decorator pattern
- Criar layers específicas (service, repository, etc)
- Separar Controller, Model, Service

---

### CS-003: Tight Coupling
**Severidade:** HIGH  
**Tipo:** Arquitetura  
**Descrição:**  
Dependências diretas e rígidas entre componentes, impossibilitando reutilização e testabilidade. Viola princípio DIP (Dependency Inversion).

**Padrão Detectável:**
- Imports/requires de implementações concretas
- Criação direta de instâncias (new/new())
- Chamadas diretas a métodos de objetos tightly coupled
- Impossível substituir um componente por outro
- Testes precisam de todo o contexto
- Sem injeção de dependência

**Impacto:**
- Impossível testar componentes isoladamente
- Impossível reutilizar código
- Mudanças em um lugar afetam tudo
- Violação de DIP (Dependency Inversion Principle)

**Refatoração:**
- Usar dependency injection
- Depender de abstrações (interfaces, protocolos)
- Injetar dependências via construtor/método
- Usar containers/factories

---

### CS-004: Long Method
**Severidade:** MEDIUM  
**Tipo:** Design  
**Descrição:**  
Função/método com muitas linhas, fazendo múltiplas coisas, difícil de entender.

**Padrão Detectável:**
- Método > 20-30 linhas
- Múltiplos níveis de indentação
- Múltiplos blocos if/for/while aninhados
- Variáveis locais complexas
- Difícil nomear a função

**Impacto:**
- Difícil de entender propósito
- Difícil de testar
- Alto risco de bugs
- Difícil de reutilizar partes da lógica

**Refatoração:**
- Extrair métodos para sub-tarefas
- Usar composição
- Aplicar strategy pattern para lógica condicional

---

### CS-005: Long Parameter List
**Severidade:** MEDIUM  
**Tipo:** Design  
**Descrição:**  
Função/método com muitos parâmetros, indicando falta de coesão.

**Padrão Detectável:**
- > 3-4 parâmetros
- Parâmetros com tipos primitivos
- Parâmetro "flag" para mudar comportamento
- Difícil de chamar sem documentação

**Impacto:**
- Difícil de usar (fácil enganar a ordem)
- Difícil de estender
- Indicador de múltiplas responsabilidades

**Refatoração:**
- Agrupar em objetos/estruturas (parameter object)
- Usar builder pattern
- Dividir em múltiplos métodos especializados

---

### CS-006: Poor Naming
**Severidade:** LOW  
**Tipo:** Qualidade  
**Descrição:**  
Variáveis, funções, classes com nomes não descritivos ou enganosos.

**Padrão Detectável:**
- Nomes genéricos: `data`, `temp`, `val`, `x`, `do_something`
- Nomes longos demais: `calculateAndUpdateAndValidateAndPersistUserWithAllTransactions`
- Nomes que mentem: `fast_cache` que é lento
- Nomes ambíguos

**Impacto:**
- Código difícil de entender
- Alto tempo de onboarding
- Mais bugs (interpretação errada)

**Refatoração:**
- Renomear para ser claro e conciso
- Usar termos de domínio (ubiquitous language)
- Evitar abreviações

---

### CS-007: Magic Numbers/Strings
**Severidade:** LOW  
**Tipo:** Manutenibilidade  
**Descrição:**  
Valores hardcoded diretamente no código sem significado claro.

**Padrão Detectável:**
- Números literais: `if (age > 18)`, `timeout = 5000`
- Strings hardcoded: `"admin"`, `"/api/v1/users"`
- Sem explicação do significado
- Repetido em múltiplos lugares

**Impacto:**
- Difícil entender o significado
- Difícil alterar valores
- Risco de inconsistência

**Refatoração:**
- Extrair para constantes nomeadas
- Usar enums para valores fixos
- Mover para configuração

---

## Categoria: SECURITY

### CS-008: SQL Injection / Command Injection
**Severidade:** CRITICAL  
**Tipo:** Segurança  
**Descrição:**  
Construir queries/comandos concatenando strings com entrada do usuário. Falha crítica de segurança.

**Padrão Detectável:**
- String concatenation em queries: `"SELECT * FROM users WHERE id = " + user_id`
- Sem validação/escape
- Template strings com entrada do usuário
- Chamadas diretas a comandos shell

**Impacto:**
- Execução de código malicioso
- Acesso não autorizado a dados
- Alteração/deleção de dados
- Comprometimento do sistema

**Refatoração:**
- Usar prepared statements/parameterized queries
- Usar ORM (Object-Relational Mapping)
- Validar e escapar entrada

---

### CS-009: Hardcoded Secrets
**Severidade:** CRITICAL  
**Tipo:** Segurança  
**Descrição:**  
Senhas, tokens, chaves criptográficas diretamente no código-fonte. Exposição crítica de credenciais.

**Padrão Detectável:**
- `api_key = "sk_live_xxx"`
- `password = "admin123"`
- `secret_key = "minha-chave-secreta"`
- Exposto em logs ou health endpoints

**Impacto:**
- Acesso não autorizado
- Exposição em repositories públicos
- Impossível rotacionar chaves facilmente

**Refatoração:**
- Usar variáveis de ambiente
- Usar cofres/vaults (AWS Secrets Manager, HashiCorp Vault)
- Nunca commitar secrets no git

---

### CS-010: Exposed Sensitive Information
**Severidade:** HIGH  
**Tipo:** Segurança  
**Descrição:**  
Informações sensíveis expostas em responses, logs ou errors.

**Padrão Detectável:**
- Stack traces com paths do sistema
- Secrets em responses de health check
- Detalhes internos em error messages
- Informações de usuário desnecessárias

**Impacto:**
- Informação para ataque
- Vazamento de dados sensíveis
- Configuração exposta

**Refatoração:**
- Mascarar stack traces em produção
- Remover detalhes internos de errors
- Usar logging estruturado e seguro

---

## Categoria: PERFORMANCE & SCALABILITY

### CS-011: N+1 Query Problem
**Severidade:** MEDIUM  
**Tipo:** Performance  
**Descrição:**  
Fazer 1 query + N queries adicionais quando poderia ser 1 só.

**Padrão Detectável:**
- Loop que executa query dentro
- Sem eager loading/joins
- Múltiplas queries para montar um objeto

**Impacto:**
- Performance degrada com mais dados
- Alto uso de banda de rede
- Timeout em grandes datasets

**Refatoração:**
- Usar joins/eager loading
- Batch queries
- Usar cache apropriado

---

### CS-012: Missing Indexes
**Severidade:** MEDIUM  
**Tipo:** Performance  
**Descrição:**  
Queries sem índices apropriados, causando table scans.

**Padrão Detectável:**
- Queries lentas em tabelas grandes
- Sem índices em colunas de filtro
- Foreign keys sem índices

**Impacto:**
- Queries lentas
- Alto uso de CPU/I/O
- Escalabilidade ruim

**Refatoração:**
- Adicionar índices em colunas frequentemente filtradas
- Índices compostos para múltiplas colunas
- Analisar query plans

---

### CS-013: Global State / Singletons
**Severidade:** HIGH  
**Tipo:** Arquitetura  
**Descrição:**  
Usar estado global ou singletons, causando problemas em concorrência e testes. Viola princípios SOLID.

**Padrão Detectável:**
- Variáveis globais
- Padrão Singleton
- Static state em classes
- Sem thread safety

**Impacto:**
- Difícil testar
- Race conditions em multi-threading
- Comportamento imprevisível
- Difícil de debugar

**Refatoração:**
- Usar dependency injection
- Evitar estado mutável global
- Thread-local storage se necessário
- Usar immutable structures

---

## Categoria: ERROR HANDLING

### CS-014: Empty Catch / Swallowing Exceptions
**Severidade:** HIGH  
**Tipo:** Confiabilidade  
**Descrição:**  
Capturar exceções sem fazer nada, escondendo erros.

**Padrão Detectável:**
```
try {
  // código
} catch (Exception e) {
  // vazio ou apenas log
}
```

**Impacto:**
- Erros silenciosos
- Difícil debugar
- Sistema continua em estado inconsistente

**Refatoração:**
- Log apropriadamente
- Propagar exceção se não souber tratar
- Tratamento específico por tipo de exceção

---

### CS-015: Inconsistent Error Handling
**Severidade:** MEDIUM  
**Tipo:** Qualidade  
**Descrição:**  
Diferentes estratégias de error handling em diferentes partes do código.

**Padrão Detectável:**
- Alguns lugares retornam erro codes
- Outros lançam exceções
- Alguns retornam null
- Sem pattern consistente

**Impacto:**
- Difícil usar a API
- Fácil esquecer tratamento
- Inconsistência entre módulos

**Refatoração:**
- Definir estratégia única
- Usar result objects / either monads
- Documentar tratamento esperado

---

## Categoria: TESTING & MAINTAINABILITY

### CS-016: Untestable Code
**Severidade:** HIGH  
**Tipo:** Testabilidade  
**Descrição:**  
Código que é muito difícil ou impossível de testar isoladamente. Viola testabilidade e SRP.

**Padrão Detectável:**
- Muitas dependências não injetáveis
- I/O direto (arquivo, rede, BD)
- Lógica misturada com framework
- Contexto global necessário
- Testes precisam de setup complexo

**Impacto:**
- Sem cobertura de testes
- Risco de regressões
- Medo de refatorar

**Refatoração:**
- Separar business logic de I/O
- Injetar dependências
- Usar padrões testáveis

---

### CS-017: Commented Out Code
**Severidade:** LOW  
**Tipo:** Manutenibilidade  
**Descrição:**  
Código comentado deixado no repositório.

**Padrão Detectável:**
- Blocos comentados
- `// TODO`, `// FIXME` antigos
- Debug code deixado

**Impacto:**
- Confusão sobre se é necessário
- Polui o código
- Git history para recuperar se necessário

**Refatoração:**
- Remover
- Usar git history se precisar recuperar
- Criar issue se for TODO real

---

## Categoria: MAINTAINABILITY

### CS-018: Missing or Outdated Documentation
**Severidade:** MEDIUM  
**Tipo:** Manutenibilidade  
**Descrição:**  
Falta de documentação ou documentação desatualizada.

**Padrão Detectável:**
- Código sem comentários
- Documentação divergente do código
- APIs sem especificação de comportamento
- Lógica complexa sem explicação

**Impacto:**
- Curva de aprendizado alta
- Manutenção mais lenta
- Risco de uso incorreto
- Onboarding mais longo

**Refatoração:**
- Adicionar comentários em lógica complexa
- Documentar APIs públicas
- Manter documentação atualizada

---

### CS-019: No Type Safety
**Severidade:** MEDIUM  
**Tipo:** Qualidade  
**Descrição:**  
Código sem type hints/annotations, perdendo segurança de tipo.

**Padrão Detectável:**
- Linguagens dinâmicas sem type hints
- Parâmetros sem tipos
- Retornos sem tipos
- Sem validação de tipo em runtime

**Impacto:**
- Bugs relacionados a tipos
- IDE não consegue ajudar
- Refatorações mais perigosas
- Documentação implícita

**Refatoração:**
- Adicionar type hints/annotations
- Usar linters estáticos (mypy, TypeScript)
- Validação em runtime quando necessário

---

### CS-020: Inconsistent Code Style
**Severidade:** LOW  
**Tipo:** Qualidade  
**Descrição:**  
Código com estilos inconsistentes de formatação e convenções.

**Padrão Detectável:**
- Indentação inconsistente
- Nomes em diferentes convenções (camelCase vs snake_case)
- Espaçamento inconsistente
- Imports desorganizados

**Impacto:**
- Difícil ler
- Dificuldades em merge/diff
- Distração visual
- Tempo gasto em discussões de estilo

**Refatoração:**
- Usar code formatter automático
- Definir linter rules
- Pre-commit hooks

---

## Como Usar Este Catálogo

1. **Ao Analisar Código:** Use este catálogo para identificar defeitos arquiteturais conhecidos
2. **Ao Documentar Issues:** Reference o ID (CS-XXX) e severidade para comunicação clara
3. **Ao Priorizar:** Considere a Severidade (CRITICAL > HIGH > MEDIUM > LOW)
4. **Ao Refatorar:** Consulte a seção de Refatoração para soluções recomendadas

## Notas

- Este catálogo é **agnóstico** de linguagem/framework, mas focado em violações de MVC e SOLID
- Baseado em princípios universais (SOLID, Clean Code, Design Patterns)
- Complementar a análises automáticas de linting/static analysis
- Severidades são diretrizes; contexto específico do projeto pode variar
