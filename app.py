
"""Vexa Store: Flask, Supabase, MongoDB e Redis."""

from __future__ import annotations

import json
import os
import re
import secrets

from datetime import timedelta
from decimal import Decimal, InvalidOperation
from functools import wraps
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

import redis
import requests

from dotenv import load_dotenv

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from PIL import Image, UnidentifiedImageError
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from werkzeug.utils import secure_filename

from clientes import instalar_rotas_clientes


# CONFIGURACOES

ROOT = Path(__file__).resolve().parent

load_dotenv(ROOT / ".env")

app = Flask(__name__)

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "dev-only-change-this-secret",
)

app.config.update(
    MAX_CONTENT_LENGTH=5 * 1024 * 1024,
    PERMANENT_SESSION_LIFETIME=timedelta(hours=3),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=(
        os.getenv(
            "SESSION_COOKIE_SECURE", "false"
        ).lower() == "true"
    ),
)

DEMO_MODE = (
    os.getenv("DEMO_MODE", "true").lower() == "true"
)

MONGO_URI = os.getenv("MONGODB_URI", "")
MONGO_DB = os.getenv("MONGODB_DB", "vexa_store")
REDIS_URL = os.getenv("REDIS_URL", "")

SUPABASE_URL = os.getenv(
    "SUPABASE_URL", ""
).rstrip("/")

SUPABASE_KEY = os.getenv(
    "SUPABASE_ANON_KEY", ""
)

ADMIN_EMAILS = {
    email.strip().lower()
    for email in os.getenv(
        "ADMIN_EMAILS", ""
    ).split(",")
    if email.strip()
}

WA_NUMBER = re.sub(
    r"\D",
    "",
    os.getenv("WHATSAPP_NUMBER", ""),
)

_mongo_client = None
_redis_client = None


# CONEXAO MONGODB

def collection():
    global _mongo_client

    if not MONGO_URI or "SEUCLUSTER" in MONGO_URI:
        raise RuntimeError(
            "Configure MONGODB_URI no .env"
        )

    if _mongo_client is None:
        _mongo_client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=4500,
        )

    return _mongo_client[MONGO_DB]["produtos"]


# CONEXAO REDIS

def redis_db():
    global _redis_client

    if not REDIS_URL:
        raise RuntimeError(
            "Configure REDIS_URL no .env"
        )

    if _redis_client is None:
        _redis_client = redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=4,
        )

    return _redis_client


# PRODUTOS

def demo_products():
    caminho = ROOT / "data/produtos_demo.json"

    return json.loads(
        caminho.read_text(encoding="utf-8")
    )


def public_product(produto):
    campos = [
        "sku",
        "nome",
        "categoria",
        "preco_centavos",
        "descricao",
        "imagem",
        "destaque",
    ]

    return {
        campo: produto.get(campo)
        for campo in campos
    }


def product_image_url(image_name):
    if not image_name:
        return url_for(
            "static",
            filename="img/placeholder.svg",
        )

    if image_name.startswith("uploads/"):
        return url_for(
            "static",
            filename=image_name,
        )

    return url_for(
        "static",
        filename="img/produtos/" + image_name,
    )


def serialize(produto):
    resultado = public_product(produto)

    resultado["imagem_url"] = product_image_url(
        resultado["imagem"]
    )

    return resultado


def fetch_all():
    if DEMO_MODE:
        return demo_products()

    return list(
        collection()
        .find({}, {"_id": 0})
        .sort("sku", 1)
    )


def find_product(sku):
    if DEMO_MODE:
        return next(
            (
                produto
                for produto in demo_products()
                if produto["sku"] == sku
            ),
            None,
        )

    return collection().find_one(
        {"sku": sku},
        {"_id": 0},
    )


# SEGURANCA ADMINISTRATIVA

def admin_required(func):

    @wraps(func)
    def inner(*args, **kwargs):

        email = session.get("admin_email")

        if not email or email not in ADMIN_EMAILS:
            return jsonify({
                "erro": (
                    "Acesso negado: autenticação "
                    "de administrador necessária."
                )
            }), 401

        return func(*args, **kwargs)

    return inner


def csrf_valid():
    recebido = (
        request.headers.get("X-CSRF-Token", "")
        or request.form.get("csrf_token", "")
    )

    esperado = session.get("csrf_token", "")

    return bool(
        recebido
        and secrets.compare_digest(
            recebido,
            esperado,
        )
    )


def csrf_required(func):

    @wraps(func)
    def inner(*args, **kwargs):

        if not csrf_valid():
            return jsonify({
                "erro": (
                    "Token de segurança inválido. "
                    "Atualize a página."
                )
            }), 403

        return func(*args, **kwargs)

    return inner


@app.after_request
def security_headers(response):

    response.headers[
        "X-Content-Type-Options"
    ] = "nosniff"

    response.headers[
        "Referrer-Policy"
    ] = "strict-origin-when-cross-origin"

    response.headers[
        "X-Frame-Options"
    ] = "DENY"

    return response


# PAGINA INICIAL

@app.get("/")
def home():
    return render_template(
        "index.html",
        demo_mode=DEMO_MODE,
        wa_number=WA_NUMBER,
    )


# DIAGNOSTICO DOS BANCOS

@app.get("/api/status")
def status():

    resultado = {
        "modo": (
            "demonstracao"
            if DEMO_MODE
            else "integrado"
        ),
        "mongodb": False,
        "redis": False,
        "supabase_configurado": bool(
            SUPABASE_URL
            and SUPABASE_KEY
            and ADMIN_EMAILS
        ),
        "whatsapp_configurado": (
            10 <= len(WA_NUMBER) <= 15
        ),
    }

    if not DEMO_MODE:

        try:
            collection().database.client.admin.command(
                "ping"
            )

            resultado["mongodb"] = True

        except (RuntimeError, PyMongoError):
            pass

        try:
            resultado["redis"] = bool(
                redis_db().ping()
            )

        except (
            RuntimeError,
            redis.RedisError,
        ):
            pass

    return jsonify(resultado)


# LISTAGEM DE PRODUTOS

@app.get("/api/products")
def get_products():

    busca = request.args.get(
        "q", ""
    ).strip().casefold()[:100]

    categoria = request.args.get(
        "categoria", ""
    ).strip().casefold()[:80]

    try:
        produtos = fetch_all()

    except (
        RuntimeError,
        PyMongoError,
    ):
        return jsonify({
            "erro": (
                "Não foi possível acessar "
                "o catálogo do MongoDB."
            )
        }), 503

    if busca:
        produtos = [
            produto
            for produto in produtos
            if busca in (
                produto.get("nome", "")
                + " "
                + produto.get("descricao", "")
            ).casefold()
        ]

    if categoria and categoria != "todos":
        produtos = [
            produto
            for produto in produtos
            if produto.get(
                "categoria", ""
            ).casefold() == categoria
        ]

    return jsonify({
        "produtos": [
            serialize(produto)
            for produto in produtos
        ],
        "total": len(produtos),
        "demo": DEMO_MODE,
    })


# DETALHES DOS PRODUTOS E REDIS

@app.get("/api/products/<string:sku>")
def get_product(sku):

    try:
        produto = find_product(sku)

    except (
        RuntimeError,
        PyMongoError,
    ):
        return jsonify({
            "erro": "Erro ao consultar MongoDB."
        }), 503

    if not produto:
        return jsonify({
            "erro": "Produto não encontrado."
        }), 404

    if not DEMO_MODE:

        try:
            visitante = session.get(
                "visitor_id"
            )

            if not visitante:
                visitante = uuid4().hex

                session["visitor_id"] = visitante

            chave = "vexa:recent:" + visitante

            pipeline = redis_db().pipeline()

            pipeline.lrem(
                chave,
                0,
                sku,
            )

            pipeline.lpush(
                chave,
                sku,
            )

            pipeline.ltrim(
                chave,
                0,
                5,
            )

            pipeline.expire(
                chave,
                60 * 60 * 24 * 30,
            )

            pipeline.execute()

        except (
            RuntimeError,
            redis.RedisError,
        ):
            return jsonify({
                "erro": (
                    "Redis indisponível: "
                    "visualização não registrada."
                )
            }), 503

    return jsonify({
        "produto": serialize(produto),
        "demo": DEMO_MODE,
    })


# HISTORICO DE PRODUTOS RECENTES

@app.get("/api/recent")
def recent():

    if DEMO_MODE:
        return jsonify({
            "produtos": [],
            "demo": True,
        })

    visitante = session.get("visitor_id")

    if not visitante:
        return jsonify({
            "produtos": [],
            "demo": False,
        })

    try:
        skus = redis_db().lrange(
            "vexa:recent:" + visitante,
            0,
            5,
        )

        produtos = [
            find_product(sku)
            for sku in skus
        ]

    except (
        RuntimeError,
        redis.RedisError,
        PyMongoError,
    ):
        return jsonify({
            "erro": (
                "Não foi possível consultar "
                "o histórico do Redis."
            )
        }), 503

    return jsonify({
        "produtos": [
            serialize(produto)
            for produto in produtos
            if produto
        ],
        "demo": False,
    })


# INSTALAR AS ROTAS DOS CLIENTES

registrar_pedido_cliente = instalar_rotas_clientes(
    app,
    redis_db,
    csrf_valid,
    supabase_url=SUPABASE_URL,
    supabase_key=SUPABASE_KEY,
    admin_emails=ADMIN_EMAILS,
    demo_mode=DEMO_MODE,
)


# FINALIZAR PEDIDO PELO WHATSAPP

@app.post("/api/checkout")
def checkout():

    if not 10 <= len(WA_NUMBER) <= 15:
        return jsonify({
            "erro": (
                "Configure WHATSAPP_NUMBER "
                "no .env com DDI e DDD."
            )
        }), 400

    payload = request.get_json(silent=True)

    carrinho = (
        payload.get("itens")
        if isinstance(payload, dict)
        else None
    )

    if (
        not isinstance(carrinho, list)
        or not 1 <= len(carrinho) <= 30
    ):
        return jsonify({
            "erro": "Carrinho inválido ou vazio."
        }), 400

    totais = []
    itens_do_pedido = []
    linhas = [
        "Olá, Vexa! Gostaria de fazer este pedido:",
        "",
    ]

    vistos = set()

    try:

        for item in carrinho:

            if not isinstance(item, dict):
                return jsonify({
                    "erro": "Item inválido no carrinho."
                }), 400

            sku = item.get("sku")
            quantidade = item.get("quantidade")

            if (
                not isinstance(sku, str)
                or not re.fullmatch(
                    r"[A-Za-z0-9-]{1,40}",
                    sku,
                )
                or type(quantidade) is not int
                or not 1 <= quantidade <= 20
                or sku in vistos
            ):
                return jsonify({
                    "erro": (
                        "Código ou quantidade inválidos."
                    )
                }), 400

            vistos.add(sku)

            produto = find_product(sku)

            if not produto:
                return jsonify({
                    "erro": (
                        f"Produto {sku} "
                        "não está mais disponível."
                    )
                }), 409

            centavos = int(
                produto["preco_centavos"]
            )

            if centavos < 0:
                return jsonify({
                    "erro": (
                        "Preço inválido no cadastro."
                    )
                }), 409

            subtotal = centavos * quantidade

            totais.append(subtotal)

            itens_do_pedido.append({
                "sku": sku,
                "nome": produto["nome"],
                "quantidade": quantidade,
                "preco_centavos": centavos,
                "subtotal_centavos": subtotal,
            })

            preco = (
                f"R$ {centavos / 100:,.2f}"
                .replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )

            valor_subtotal = (
                f"R$ {subtotal / 100:,.2f}"
                .replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )

            linhas.append(
                f"• {produto['nome']} ({sku}) "
                f"— {quantidade} x {preco} "
                f"= {valor_subtotal}"
            )

    except (
        RuntimeError,
        PyMongoError,
        KeyError,
        TypeError,
        ValueError,
    ):
        return jsonify({
            "erro": (
                "Não foi possível consultar "
                "os preços no MongoDB."
            )
        }), 503

    total_centavos = sum(totais)

    total_formatado = (
        f"R$ {total_centavos / 100:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )

    linhas += [
        "",
        f"Total estimado: {total_formatado}",
        "",
        (
            "Por favor, informe disponibilidade, "
            "entrega e pagamento."
        ),
    ]

    mensagem = "\n".join(linhas)

    link = (
        f"https://wa.me/{WA_NUMBER}"
        f"?text={quote(mensagem)}"
    )

    registro = registrar_pedido_cliente(
        itens_do_pedido,
        total_centavos,
    )

    return jsonify({
        "url": link,
        "total_centavos": total_centavos,
        "registro_cliente": registro,
    })


# LOGIN DO ADMINISTRADOR

@app.route(
    "/admin/login",
    methods=["GET", "POST"],
)
def admin_login():

    erro = ""

    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(
            24
        )

    if (
        request.method == "POST"
        and not csrf_valid()
    ):
        erro = (
            "Formulário expirado. "
            "Atualize a página e tente novamente."
        )

    elif request.method == "POST":

        email = request.form.get(
            "email", ""
        ).strip().lower()

        senha = request.form.get(
            "password", ""
        )

        if DEMO_MODE:
            erro = (
                "O login real exige DEMO_MODE=false "
                "e as credenciais do Supabase no .env."
            )

        elif not (
            SUPABASE_URL
            and SUPABASE_KEY
            and ADMIN_EMAILS
        ):
            erro = (
                "Configure SUPABASE_URL, "
                "SUPABASE_ANON_KEY e ADMIN_EMAILS "
                "no .env."
            )

        elif email not in ADMIN_EMAILS:
            erro = (
                "Esta conta não tem permissão "
                "de administrador."
            )

        else:

            try:
                resposta = requests.post(
                    SUPABASE_URL
                    + "/auth/v1/token?grant_type=password",
                    headers={
                        "apikey": SUPABASE_KEY,
                        "Content-Type": "application/json",
                    },
                    json={
                        "email": email,
                        "password": senha,
                    },
                    timeout=12,
                )

                resultado = resposta.json()

                usuario = (
                    resultado.get("user") or {}
                )

                if (
                    resposta.ok
                    and resultado.get("access_token")
                    and usuario.get(
                        "email", ""
                    ).lower() == email
                ):
                    session.clear()
                    session.permanent = True

                    session["admin_email"] = email

                    session["csrf_token"] = (
                        secrets.token_urlsafe(24)
                    )

                    return redirect(
                        url_for("admin")
                    )

                erro = (
                    "E-mail ou senha incorretos, "
                    "ou conta sem acesso."
                )

            except (
                requests.RequestException,
                ValueError,
            ):
                erro = (
                    "Não foi possível conectar "
                    "ao Supabase."
                )

    return render_template(
        "login.html",
        error=erro,
        demo_mode=DEMO_MODE,
        csrf=session["csrf_token"],
    )


# PAINEL ADMINISTRATIVO

@app.get("/admin")
def admin():

    email = session.get("admin_email")

    if not email or email not in ADMIN_EMAILS:
        return redirect(
            url_for("admin_login")
        )

    return render_template(
        "admin.html",
        preview=False,
        admin_email=email,
        csrf=session.get("csrf_token", ""),
    )


# PREVIA ADMINISTRATIVA

@app.get("/admin/preview")
def admin_preview():

    return render_template(
        "admin.html",
        preview=True,
        admin_email="Prévia visual",
        csrf="",
    )


# SAIR DA CONTA DO ADMINISTRADOR

@app.post("/admin/logout")
@admin_required
@csrf_required
def admin_logout():

    session.clear()

    return jsonify({"ok": True})


# VALIDAR CADASTRO DE PRODUTOS

def parse_product_form():

    nome = request.form.get(
        "nome", ""
    ).strip()[:120]

    categoria = request.form.get(
        "categoria", ""
    ).strip()[:50]

    descricao = request.form.get(
        "descricao", ""
    ).strip()[:500]

    sku = request.form.get(
        "sku", ""
    ).strip().upper()[:40]

    if not nome or not categoria:
        raise ValueError(
            "Nome e categoria são obrigatórios."
        )

    if sku and not re.fullmatch(
        r"[A-Z0-9-]+",
        sku,
    ):
        raise ValueError(
            "O código do produto deve conter apenas "
            "letras, números e hífens."
        )

    try:
        preco = Decimal(
            request.form.get(
                "preco", ""
            ).replace(",", ".")
        )

        if (
            not preco.is_finite()
            or preco < 0
            or preco > Decimal("999999")
        ):
            raise ValueError()

        centavos = int(
            (preco * 100).quantize(
                Decimal("1")
            )
        )

    except (
        InvalidOperation,
        ValueError,
    ):
        raise ValueError(
            "Digite um preço válido."
        )

    dados = {
        "nome": nome,
        "categoria": categoria,
        "descricao": descricao,
        "preco_centavos": centavos,
        "destaque": (
            request.form.get("destaque") == "true"
        ),
    }

    return dados, sku


# UPLOAD DAS FOTOS DOS PRODUTOS

def handle_image_upload(current=""):

    arquivo = request.files.get("imagem")

    if not arquivo or not arquivo.filename:
        return current

    nome_seguro = secure_filename(
        arquivo.filename
    )

    if not nome_seguro.lower().endswith(
        (".png", ".jpg", ".jpeg", ".webp")
    ):
        raise ValueError(
            "Envie uma imagem PNG, JPG ou WebP."
        )

    try:
        imagem = Image.open(
            arquivo.stream
        )

        imagem.verify()

        arquivo.stream.seek(0)

        imagem = Image.open(
            arquivo.stream
        )

        imagem.thumbnail(
            (1250, 1250)
        )

        nome_final = (
            uuid4().hex + ".webp"
        )

        destino = (
            ROOT
            / "static/uploads"
            / nome_final
        )

        imagem.convert("RGB").save(
            destino,
            "WEBP",
            quality=86,
        )

        return "uploads/" + nome_final

    except (
        UnidentifiedImageError,
        OSError,
    ):
        raise ValueError(
            "Arquivo de imagem inválido."
        )


# CADASTRAR NOVO PRODUTO

@app.post("/api/admin/products")
@admin_required
@csrf_required
def add_product():

    if DEMO_MODE:
        return jsonify({
            "erro": (
                "Cadastro desabilitado "
                "em modo demonstração."
            )
        }), 409

    try:
        dados, sku = parse_product_form()

        sku = (
            sku
            or "VEX-" + uuid4().hex[:8].upper()
        )

        if collection().find_one({
            "sku": sku
        }):
            return jsonify({
                "erro": (
                    "Já existe um produto "
                    "com este código."
                )
            }), 409

        dados["sku"] = sku

        dados["imagem"] = (
            handle_image_upload()
        )

        collection().insert_one(
            dados
        )

        return jsonify({
            "produto": serialize(dados),
            "ok": True,
        }), 201

    except ValueError as erro:
        return jsonify({
            "erro": str(erro)
        }), 400

    except (
        RuntimeError,
        PyMongoError,
    ):
        return jsonify({
            "erro": (
                "Falha ao cadastrar no MongoDB."
            )
        }), 503


# EDITAR PRODUTO

@app.put("/api/admin/products/<string:sku>")
@admin_required
@csrf_required
def update_product(sku):

    if DEMO_MODE:
        return jsonify({
            "erro": (
                "Edição desabilitada "
                "em modo demonstração."
            )
        }), 409

    try:
        antigo = collection().find_one(
            {"sku": sku},
            {"_id": 0},
        )

        if not antigo:
            return jsonify({
                "erro": "Produto não encontrado."
            }), 404

        dados, _ = parse_product_form()

        dados["imagem"] = (
            handle_image_upload(
                antigo.get("imagem", "")
            )
        )

        collection().update_one(
            {"sku": sku},
            {"$set": dados},
        )

        antigo.update(dados)

        return jsonify({
            "ok": True,
            "produto": serialize(antigo),
        })

    except ValueError as erro:
        return jsonify({
            "erro": str(erro)
        }), 400

    except (
        RuntimeError,
        PyMongoError,
    ):
        return jsonify({
            "erro": (
                "Falha ao atualizar no MongoDB."
            )
        }), 503


# EXCLUIR PRODUTO

@app.delete("/api/admin/products/<string:sku>")
@admin_required
@csrf_required
def delete_product(sku):

    if DEMO_MODE:
        return jsonify({
            "erro": (
                "Exclusão desabilitada "
                "em modo demonstração."
            )
        }), 409

    try:
        resultado = collection().delete_one({
            "sku": sku
        })

    except (
        RuntimeError,
        PyMongoError,
    ):
        return jsonify({
            "erro": (
                "Falha ao excluir no MongoDB."
            )
        }), 503

    if not resultado.deleted_count:
        return jsonify({
            "erro": "Produto não encontrado."
        }), 404

    return jsonify({
        "ok": True
    })


# LIMITE DE TAMANHO DAS FOTOS

@app.errorhandler(413)
def too_large(_error):

    return jsonify({
        "erro": (
            "A imagem deve ter no máximo 5 MB."
        )
    }), 413


# INICIAR SERVIDOR

if __name__ == "__main__":

    if (
        not DEMO_MODE
        and app.secret_key in {
            "dev-only-change-this-secret",
            "troque-por-uma-chave-longa-e-aleatoria",
        }
    ):
        raise SystemExit(
            "Defina uma FLASK_SECRET_KEY longa "
            "e aleatória no .env antes de "
            "ativar os bancos reais."
        )

    if app.secret_key == "dev-only-change-this-secret":
        print(
            "ATENÇÃO: defina FLASK_SECRET_KEY "
            "no .env antes de acessar em rede."
        )

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
    )
