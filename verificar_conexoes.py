
"""VEXA - Diagnóstico das conexões dos bancos de dados."""

import requests

from app import (
    collection,
    redis_db,
    SUPABASE_URL,
    SUPABASE_KEY,
    DEMO_MODE,
)


def verificar(nome, funcao):
    try:
        funcao()
        print(f"[OK] {nome} - Conectado")
        return True

    except Exception as erro:
        print(f"[ERRO] {nome} - Falha na conexão")
        print(f"       Tipo: {type(erro).__name__}")
        return False


def testar_mongodb():
    banco = collection().database.client
    banco.admin.command("ping")


def testar_redis():
    resposta = redis_db().ping()

    if not resposta:
        raise ConnectionError("Redis não respondeu.")


def testar_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Supabase não configurado.")

    resposta = requests.get(
        f"{SUPABASE_URL}/auth/v1/health",
        headers={"apikey": SUPABASE_KEY},
        timeout=10,
    )

    resposta.raise_for_status()

    dados = resposta.json()

    if dados.get("name") not in ("GoTrue", "Auth"):
        raise ConnectionError(
            "Resposta inesperada do Supabase Auth."
        )


print("=" * 48)
print("           VEXA E-COMMERCE")
print("       DIAGNÓSTICO DOS BANCOS")
print("=" * 48)

print()

mongo = verificar("MongoDB", testar_mongodb)
redis_ok = verificar("Redis", testar_redis)
supabase = verificar("Supabase Auth", testar_supabase)

print()
print("=" * 48)

if mongo and redis_ok and supabase:
    print("SUCESSO: Os três serviços responderam!")
else:
    print("ATENÇÃO: Verifique as conexões com erro.")

if DEMO_MODE:
    print("AVISO: O modo demonstração está ativado.")
else:
    print("Modo integrado ativado.")

print("=" * 48)

print("Nota: o login e as operações de cadastro")
print("precisam ser testados separadamente.")
