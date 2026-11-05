
# Vexa Store — Sistema de E-commerce

**Aluno:** Ronald Machado  
**Professor:** Anderson Soares  
**Disciplina:** Projeto Banco de Dados  
**Atividade:** 3ª Avaliação — 2026

## Sobre o projeto

A Vexa Store é um sistema de e-commerce desenvolvido em Python com Flask, utilizando o conceito de Banco de Dados Poliglota. O projeto integra Supabase, MongoDB Atlas e Redis Cloud, distribuindo as responsabilidades de armazenamento conforme as funcionalidades da aplicação.

O sistema conta com catálogo de produtos, painel administrativo, carrinho de compras, cadastro de clientes e preparação de pedidos para o WhatsApp.

A interface foi desenvolvida com HTML, CSS e JavaScript, seguindo uma identidade visual em azul e branco. O logotipo da Vexa foi criado manualmente no Canva.

<p align="center">
  <img src="docs/imagens/01-pagina-inicial.png" width="900" alt="Página inicial da Vexa">
</p>

## Tecnologias e bancos de dados

| Tecnologia | Utilização |
|---|---|
| Python e Flask | Backend e funcionamento da aplicação |
| HTML, CSS e JavaScript | Interface web e interatividade |
| Supabase Auth | Autenticação do administrador e dos clientes |
| PostgreSQL (Supabase) | Armazenamento de perfis e pedidos preparados |
| MongoDB Atlas | Cadastro, consulta, edição e exclusão de produtos |
| Redis Cloud | Cache dos produtos visualizados e sessões temporárias |
| WhatsApp | Redirecionamento com mensagem do pedido |
| Canva | Criação manual do logotipo |

### Organização dos dados

**Supabase:** responsável pela autenticação e pelas informações relacionadas aos clientes. Além da estrutura `auth.users`, foram criadas as tabelas `vexa_clientes` e `vexa_pedidos`, com relacionamentos e políticas de segurança RLS.

O código SQL utilizado está disponível em [SUPABASE_CLIENTES.sql](SUPABASE_CLIENTES.sql).

**MongoDB Atlas:** utilizado para armazenar os produtos no banco `vexa_store`, coleção `produtos`. Cada produto possui informações como código, nome, categoria, descrição, preço, imagem e destaque.

**Redis Cloud:** responsável pelo armazenamento temporário dos produtos visualizados recentemente, além de auxiliar no gerenciamento das sessões de clientes.

## Funcionalidades do sistema

A loja permite visualizar os produtos disponíveis, pesquisar itens, navegar por categorias e adicionar produtos ao carrinho. O usuário pode alterar as quantidades, remover itens e consultar o valor total da compra.

A finalização gera uma mensagem com os produtos selecionados, suas quantidades e o valor total, redirecionando o usuário para o WhatsApp. O sistema não realiza pagamentos diretamente.

### Catálogo e carrinho

<p align="center">
  <img src="docs/imagens/02-categorias.png" width="48%" alt="Categorias">
  <img src="docs/imagens/03-catalogo.png" width="48%" alt="Catálogo">
</p>

<p align="center">
  <img src="docs/imagens/04-carrinho.png" width="850" alt="Carrinho de compras">
</p>

### Cadastro e acesso dos clientes

Foi implementada uma área de clientes integrada ao Supabase, permitindo criar uma conta, realizar login, atualizar o nome e consultar o histórico dos pedidos preparados.

<p align="center">
  <img src="docs/imagens/05-login-cliente.png" width="48%" alt="Login do cliente">
  <img src="docs/imagens/06-minha-conta.png" width="48%" alt="Área do cliente">
</p>

### Administração

O painel administrativo possui autenticação restrita pelo Supabase e permite gerenciar os produtos armazenados no MongoDB.

O administrador pode cadastrar, editar, consultar e excluir produtos, além de visualizar informações gerais do catálogo. Os produtos cadastrados ficam disponíveis na vitrine da loja.

<p align="center">
  <img src="docs/imagens/12-login-administrador.png" width="850" alt="Login administrativo">
</p>

<p align="center">
  <img src="docs/imagens/07-painel-admin.png" width="48%" alt="Painel administrativo">
  <img src="docs/imagens/08-listagem-admin.png" width="48%" alt="Lista de produtos">
</p>

<p align="center">
  <img src="docs/imagens/09-cadastro-produto.png" width="48%" alt="Cadastro de produto">
  <img src="docs/imagens/11-editar-produto.png" width="48%" alt="Edição de produto">
</p>

## Estrutura do projeto

```text
vexa-sistema/
├── app.py
├── clientes.py
├── seed.py
├── verificar_conexoes.py
├── verificar_historico.py
├── testes_basicos.py
├── SUPABASE_CLIENTES.sql
├── requirements.txt
├── .env.example
├── iniciar_windows.bat
├── templates/
├── static/
├── data/
├── docs/
│   └── imagens/
└── README.md
```

O `app.py` concentra a aplicação Flask e as rotas principais. O `clientes.py` implementa as funcionalidades de autenticação e gerenciamento dos clientes. O `seed.py` permite carregar os produtos iniciais no MongoDB.

As páginas HTML estão em `templates`, enquanto os arquivos CSS, JavaScript e as imagens utilizadas pela loja estão em `static`. A pasta `data` contém os dados de demonstração.

## Configuração e execução

O projeto foi desenvolvido em ambiente Windows, utilizando Python 3.11 e Visual Studio Code.

**1. Instalar as dependências**

Abra o terminal na pasta do projeto e execute:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**2. Configurar os bancos de dados**

Crie o arquivo `.env` com base no `.env.example` e preencha as credenciais do Supabase, MongoDB Atlas e Redis Cloud, além do número de WhatsApp da loja.

Configure `DEMO_MODE=false` para utilizar as conexões reais.

No Supabase, execute o arquivo `SUPABASE_CLIENTES.sql` pelo SQL Editor para criar as tabelas e as políticas de acesso, caso ainda não estejam configuradas.

Para carregar os produtos iniciais no MongoDB, utilize:

```powershell
.\.venv\Scripts\python.exe seed.py
```

**3. Verificar as conexões**

```powershell
.\.venv\Scripts\python.exe verificar_conexoes.py
```

Durante os testes, os três serviços responderam corretamente:

```text
[OK] MongoDB - Conectado
[OK] Redis - Conectado
[OK] Supabase Auth - Conectado

SUCESSO: Os três serviços responderam!
Modo integrado ativado.
```

<p align="center">
  <img src="docs/imagens/10-conexoes.png" width="850" alt="Diagnóstico das conexões">
</p>

**4. Iniciar o sistema**

```powershell
.\.venv\Scripts\python.exe -c "from app import app; app.run(host='127.0.0.1', port=5001, debug=False)"
```


## Vídeo de demonstração

**Vídeo da 3ª Avaliação:**

[[link do vídeo](https://drive.google.com/file/d/10MB6k9dIEQ6-mY4GZRyoOa6r_H3iUkx4/view?usp=sharing)]

A demonstração apresenta o login do administrador, o cadastro de um novo produto com atualização no catálogo e a simulação da compra com redirecionamento para o WhatsApp.

---

**Ronald Machado — Projeto Banco de Dados — 2026**
