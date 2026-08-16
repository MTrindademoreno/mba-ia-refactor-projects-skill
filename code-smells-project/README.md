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