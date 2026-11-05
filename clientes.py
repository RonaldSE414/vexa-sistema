
from __future__ import annotations

import json
import re
import secrets
import time

from functools import wraps

import redis
import requests

from flask import (
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)


CLIENT_SESSION_TTL = 3 * 60 * 60
CLIENT_KEY_PREFIX = "vexa:cliente:sessao:"


def instalar_rotas_clientes(
    app,
    redis_db,
    csrf_valid,
    supabase_url,
    supabase_key,
    admin_emails,
    demo_mode=False,
):
    base_url = supabase_url.rstrip("/")

    headers = {
        "apikey": supabase_key,
        "Content-Type": "application/json",
    }

    configured = bool(
        base_url and supabase_key and not demo_mode
    )

    def ensure_csrf():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_urlsafe(24)

        return session["csrf_token"]

    def auth_request(endpoint, body):
        return requests.post(
            base_url + endpoint,
            headers=headers,
            json=body,
            timeout=12,
        )

    def token_current():
        sid = session.get("cliente_sid", "")

        if not sid or not session.get("cliente_id"):
            return None

        try:
            db = redis_db()

            raw = db.get(CLIENT_KEY_PREFIX + sid)

            if not raw:
                return None

            tokens = json.loads(raw)

            if tokens.get("valid_until", 0) > time.time() + 45:
                return tokens["access_token"]

            refreshed = auth_request(
                "/auth/v1/token?grant_type=refresh_token",
                {
                    "refresh_token": tokens.get(
                        "refresh_token", ""
                    )
                },
            )

            if not refreshed.ok:
                db.delete(CLIENT_KEY_PREFIX + sid)
                return None

            value = refreshed.json()

            if not value.get("access_token"):
                return None

            tokens = {
                "access_token": value["access_token"],
                "refresh_token": value.get(
                    "refresh_token",
                    tokens["refresh_token"],
                ),
                "valid_until": time.time()
                + int(value.get("expires_in", 3600)),
            }

            db.setex(
                CLIENT_KEY_PREFIX + sid,
                CLIENT_SESSION_TTL,
                json.dumps(tokens),
            )

            return tokens["access_token"]

        except (
            requests.RequestException,
            redis.RedisError,
            RuntimeError,
            ValueError,
            KeyError,
            TypeError,
        ):
            return None

    def data_request(
        method,
        table,
        token,
        *,
        params=None,
        body=None,
        prefer=None,
    ):
        auth_headers = {
            **headers,
            "Authorization": "Bearer " + token,
        }

        if prefer:
            auth_headers["Prefer"] = prefer

        return requests.request(
            method,
            base_url + "/rest/v1/" + table,
            headers=auth_headers,
            params=params,
            json=body,
            timeout=12,
        )

    def client_required(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if (
                not session.get("cliente_id")
                or not token_current()
            ):
                return redirect(url_for("cliente_login"))

            return fn(*args, **kwargs)

        return wrapped

    def persist_tokens(payload):
        user = payload.get("user") or {}

        uid = user.get("id")
        email = (user.get("email") or "").lower()

        if not (
            uid
            and email
            and payload.get("access_token")
            and payload.get("refresh_token")
        ):
            return False

        if email in admin_emails:
            return False

        sid = secrets.token_urlsafe(32)

        tokens = {
            "access_token": payload["access_token"],
            "refresh_token": payload["refresh_token"],
            "valid_until": time.time()
            + int(payload.get("expires_in", 3600)),
        }

        redis_db().setex(
            CLIENT_KEY_PREFIX + sid,
            CLIENT_SESSION_TTL,
            json.dumps(tokens),
        )

        session.clear()
        session.permanent = True

        session["cliente_sid"] = sid
        session["cliente_id"] = uid
        session["cliente_email"] = email
        session["visitor_id"] = "cliente_" + uid
        session["csrf_token"] = secrets.token_urlsafe(24)

        return True

    # CADASTRO DE CLIENTES

    @app.route(
        "/cliente/cadastro",
        methods=["GET", "POST"],
    )
    def cliente_cadastro():
        erro = ""
        token = ensure_csrf()

        if request.method == "POST":

            if not csrf_valid():
                erro = (
                    "Formulário expirado. Atualize a página."
                )

            elif not configured:
                erro = (
                    "Ative o modo integrado e configure "
                    "o Supabase no .env."
                )

            else:
                nome = request.form.get(
                    "nome", ""
                ).strip()

                email = request.form.get(
                    "email", ""
                ).strip().lower()

                senha = request.form.get("senha", "")

                if (
                    not 2 <= len(nome) <= 100
                    or not re.fullmatch(
                        r"[^\s@]+@[^\s@]+\.[^\s@]+",
                        email,
                    )
                ):
                    erro = "Informe nome e e-mail válidos."

                elif len(senha) < 8:
                    erro = (
                        "A senha deve ter pelo menos "
                        "8 caracteres."
                    )

                elif email in admin_emails:
                    erro = (
                        "Esta conta é reservada ao "
                        "administrador. Utilize outro e-mail."
                    )

                else:
                    try:
                        response = auth_request(
                            "/auth/v1/signup",
                            {
                                "email": email,
                                "password": senha,
                                "data": {"nome": nome},
                            },
                        )

                        if response.ok:
                            return redirect(
                                url_for(
                                    "cliente_login",
                                    cadastrado="1",
                                )
                            )

                        data = response.json()

                        erro = (
                            data.get("msg")
                            or data.get("message")
                            or data.get("error_description")
                            or "Não foi possível realizar o cadastro."
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
            "cliente_auth.html",
            titulo="Criar minha conta",
            registro=True,
            erro=erro,
            csrf=token,
        )

    # LOGIN DOS CLIENTES

    @app.route(
        "/cliente/login",
        methods=["GET", "POST"],
    )
    def cliente_login():
        erro = ""
        token = ensure_csrf()

        if request.method == "POST":

            if not csrf_valid():
                erro = (
                    "Formulário expirado. Atualize a página."
                )

            elif not configured:
                erro = (
                    "Ative o modo integrado e configure "
                    "o Supabase no .env."
                )

            else:
                email = request.form.get(
                    "email", ""
                ).strip().lower()

                senha = request.form.get("senha", "")

                if email in admin_emails:
                    erro = (
                        "Administradores devem entrar "
                        "pelo painel administrativo."
                    )

                else:
                    try:
                        response = auth_request(
                            "/auth/v1/token?grant_type=password",
                            {
                                "email": email,
                                "password": senha,
                            },
                        )

                        payload = response.json()

                        if (
                            response.ok
                            and persist_tokens(payload)
                        ):
                            try:
                                user = payload.get("user") or {}

                                metadata = (
                                    user.get("user_metadata") or {}
                                )

                                nome = (
                                    metadata.get("nome")
                                    or "Cliente Vexa"
                                )

                                data_request(
                                    "POST",
                                    "vexa_clientes",
                                    token_current(),
                                    params={
                                        "on_conflict": "id"
                                    },
                                    body={
                                        "id": session["cliente_id"],
                                        "nome": str(nome)[:100],
                                    },
                                    prefer=(
                                        "resolution=ignore-duplicates,"
                                        "return=minimal"
                                    ),
                                )

                            except (
                                requests.RequestException,
                                RuntimeError,
                                ValueError,
                            ):
                                pass

                            return redirect(
                                url_for("cliente_conta")
                            )

                        erro = (
                            "E-mail ou senha incorretos, "
                            "ou e-mail ainda não confirmado."
                        )

                    except (
                        requests.RequestException,
                        redis.RedisError,
                        RuntimeError,
                        ValueError,
                        TypeError,
                    ):
                        erro = (
                            "Não foi possível conectar "
                            "ao Supabase ou Redis."
                        )

        return render_template(
            "cliente_auth.html",
            titulo="Entrar na minha conta",
            registro=False,
            erro=erro,
            csrf=token,
            cadastrado=(
                request.args.get("cadastrado") == "1"
            ),
        )

    # ÁREA MINHA CONTA

    @app.get("/cliente")
    @client_required
    def cliente_conta():
        erro = ""
        nome = ""
        pedidos = []

        token = token_current()

        try:
            perfil = data_request(
                "GET",
                "vexa_clientes",
                token,
                params={
                    "select": "nome",
                    "id": "eq." + session["cliente_id"],
                },
            )

            historico = data_request(
                "GET",
                "vexa_pedidos",
                token,
                params={
                    "select": (
                        "id,itens,total_centavos,"
                        "status,criado_em"
                    ),
                    "cliente_id": (
                        "eq." + session["cliente_id"]
                    ),
                    "order": "criado_em.desc",
                    "limit": "20",
                },
            )

            if perfil.ok and historico.ok:
                rows = perfil.json()

                nome = rows[0]["nome"] if rows else ""
                pedidos = historico.json()

            else:
                erro = (
                    "Não foi possível consultar os dados. "
                    "Confira se executou o SQL no Supabase."
                )

        except (
            requests.RequestException,
            ValueError,
            TypeError,
        ):
            erro = (
                "Não foi possível consultar "
                "as informações da conta."
            )

        return render_template(
            "cliente_conta.html",
            nome=nome,
            email=session.get("cliente_email"),
            pedidos=pedidos,
            erro=erro,
            csrf=ensure_csrf(),
        )

    # ALTERAR NOME DO CLIENTE

    @app.post("/cliente/perfil")
    @client_required
    def cliente_perfil():
        if not csrf_valid():
            return redirect(url_for("cliente_conta"))

        nome = request.form.get(
            "nome", ""
        ).strip()

        if 2 <= len(nome) <= 100:
            try:
                data_request(
                    "PATCH",
                    "vexa_clientes",
                    token_current(),
                    params={
                        "id": "eq." + session["cliente_id"]
                    },
                    body={"nome": nome},
                    prefer="return=minimal",
                )

            except (
                requests.RequestException,
                RuntimeError,
            ):
                pass

        return redirect(url_for("cliente_conta"))

    # SAIR DA CONTA

    @app.post("/cliente/sair")
    def cliente_sair():
        if csrf_valid():
            sid = session.get("cliente_sid")

            if sid:
                try:
                    redis_db().delete(
                        CLIENT_KEY_PREFIX + sid
                    )

                except (
                    redis.RedisError,
                    RuntimeError,
                ):
                    pass

            session.clear()

        return redirect(url_for("home"))

    # SALVAR PEDIDO PREPARADO NO SUPABASE

    def registrar_pedido_cliente(
        itens,
        total_centavos,
    ):
        if not session.get("cliente_id"):
            return None

        token = token_current()

        if not token:
            return False

        try:
            response = data_request(
                "POST",
                "vexa_pedidos",
                token,
                body={
                    "cliente_id": session["cliente_id"],
                    "itens": itens,
                    "total_centavos": total_centavos,
                    "status": "preparado",
                },
                prefer="return=minimal",
            )

            return response.ok

        except (
            requests.RequestException,
            ValueError,
        ):
            return False

    return registrar_pedido_cliente
