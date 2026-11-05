
# Vexa Store 🛍️

**E-commerce desenvolvido com Python e Flask, utilizando Banco de Dados Poliglota.**

**Aluno:** Ronald Machado  
**Professor:** Anderson Soares  
**Disciplina:** Projeto Banco de Dados  
**Atividade:** 3ª Avaliação — 2026

<p align="center">
  <img src="docs/imagens/01-pagina-inicial.png" alt="Página inicial da Vexa" width="850">
</p>

## Sobre o projeto

A **Vexa Store** é um sistema de e-commerce com catálogo de produtos, carrinho de compras, painel administrativo e finalização de pedidos pelo WhatsApp.

O projeto utiliza três tecnologias de banco de dados, cada uma com uma finalidade específica: **Supabase (PostgreSQL)**, **MongoDB Atlas** e **Redis Cloud**.

### Tecnologias utilizadas

- **Python e Flask:** desenvolvimento do backend.
- **HTML, CSS, JavaScript e Jinja2:** interface web responsiva.
- **Supabase Auth e PostgreSQL:** autenticação e dados de clientes.
- **MongoDB Atlas:** armazenamento e gerenciamento de produtos.
- **Redis Cloud:** cache de produtos visualizados e sessões temporárias.
- **PyMongo, redis-py, Requests, Pillow e python-dotenv:** integrações e funcionalidades auxiliares.
- **Canva:** criação manual do logotipo da Vexa.
- **Git e GitHub:** versionamento e organização do projeto.

## Bancos de dados

| Banco | Utilização |
|---|---|
| **Supabase** | Login do administrador e clientes, perfis e histórico de pedidos preparados. |
| **MongoDB Atlas** | Cadastro, consulta, edição e exclusão de produtos no banco `vexa_store`, coleção `produtos`. |
| **Redis Cloud** | Armazenamento temporário dos produtos visualizados recentemente e das sessões de clientes. |

### Estrutura do PostgreSQL

Além da estrutura `auth.users`, gerenciada pelo Supabase Auth, foram utilizadas duas tabelas:

**`vexa_clientes`**
- `id` — UUID, chave primária e referência a `auth.users`.
- `nome` — nome do cliente.
- `criado_em` — data do cadastro.

**`vexa_pedidos`**
- `id` — UUID, identificador do pedido.
- `cliente_id` — referência ao usuário autenticado.
- `itens` — JSONB contendo os produtos.
- `total_centavos` — valor total em centavos.
- `status` — situação do pedido.
- `criado_em` — data de criação.

As tabelas utilizam **Row Level Security (RLS)** para restringir o acesso aos dados do próprio cliente.

O script de criação das tabelas, relacionamentos, índice e políticas está disponível em:

**[SUPABASE_CLIENTES.sql](SUPABASE_CLIENTES.sql)**

## Funcionalidades

### Administração
- Login restrito utilizando Supabase Auth.
- Painel com indicadores do catálogo.
- Cadastro, edição, consulta e exclusão de produtos no MongoDB.
- Gerenciamento de nome, descrição, categoria, preço, SKU, imagem e destaque.

### Loja e clientes
- Catálogo com pesquisa e filtros por categoria.
- Visualização detalhada dos produtos.
- Carrinho com quantidade, remoção de itens e cálculo automático do total.
- Redirecionamento para o WhatsApp com mensagem do pedido formatada.
- Cadastro e login de clientes pelo Supabase.
- Perfil do cliente e histórico de pedidos preparados.
- Histórico de produtos visualizados utilizando Redis.

O sistema prepara o pedido para o WhatsApp, sem processar pagamentos.

## Como executar

**1. Instalar as dependências**

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**2. Configurar os bancos**

Copie `.env.example` para `.env` e preencha as credenciais do Supabase, MongoDB e Redis, além do número do WhatsApp.

Configure `DEMO_MODE=false` para utilizar os serviços reais.

No SQL Editor do Supabase, execute o conteúdo de `SUPABASE_CLIENTES.sql`.

Para carregar os produtos iniciais no MongoDB, se necessário:

```powershell
.\.venv\Scripts\python.exe seed.py
```

**3. Verificar as conexões**

```powershell
.\.venv\Scripts\python.exe verificar_conexoes.py
```

**4. Executar a aplicação**

```powershell
.\.venv\Scripts\python.exe -c "from app import app; app.run(host='127.0.0.1', port=5001, debug=False)"
```

**Acessos locais:**

- Loja: http://127.0.0.1:5001
- Administrador: http://127.0.0.1:5001/admin/login
- Cadastro de clientes: http://127.0.0.1:5001/cliente/cadastro

O arquivo `.env` contém credenciais privadas e não deve ser publicado no GitHub.

## Telas do sistema

### Página inicial

![Página inicial da Vexa](docs/imagens/01-pagina-inicial.png)

### Categorias e catálogo

| Categorias | Produtos |
|---|---|
| ![Categorias](docs/imagens/02-categorias.png) | ![Catálogo](docs/imagens/03-catalogo.png) |

### Carrinho de compras

![Carrinho de compras](docs/imagens/04-carrinho.png)

### Área do cliente

| Login do cliente | Perfil e pedidos |
|---|---|
| ![Login do cliente](docs/imagens/05-login-cliente.png) | ![Perfil do cliente](docs/imagens/06-minha-conta.png) |

### Login administrativo

![Login administrativo](docs/imagens/12-login-administrador.png)

### Painel administrativo

| Visão geral | Lista de produtos |
|---|---|
| ![Painel](docs/imagens/07-painel-admin.png) | ![Produtos](docs/imagens/08-listagem-admin.png) |

### Cadastro e edição de produtos

| Cadastrar produto | Editar produto |
|---|---|
| ![Cadastro](docs/imagens/09-cadastro-produto.png) | ![Edição](docs/imagens/11-editar-produto.png) |

### Verificação dos bancos de dados

![MongoDB, Redis e Supabase conectados](docs/imagens/10-conexoes.png)

O diagnóstico demonstrou a conexão com os três serviços utilizados pela aplicação.

## Vídeo de demonstração

**Vídeo da 3ª Avaliação:**
(https://drive.google.com/file/d/10MB6k9dIEQ6-mY4GZRyoOa6r_H3iUkx4/view?usp=sharing)

A demonstração deverá apresentar o login administrativo, o cadastro de um produto com atualização do catálogo e uma compra simulada com redirecionamento para o WhatsApp.

---

**Ronald Machado | Projeto Banco de Dados | Professor Anderson Soares | 2026**
