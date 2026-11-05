"""Exibe, para a demonstração, as listas de produtos vistos armazenadas no Redis real."""
from app import redis_db

if __name__ == '__main__':
    try:
        redis = redis_db()
        redis.ping()
        keys = sorted(redis.scan_iter(match='vexa:recent:*', count=100))
        if not keys:
            print('Redis conectado, mas ainda não há visualizações. Abra produtos na loja no modo integrado.')
        for key in keys[:20]:
            print(f'{key}: {redis.lrange(key, 0, -1)}')
        if len(keys) > 20:
            print(f'(Mostradas 20 de {len(keys)} listas)')
    except Exception as exc:
        print(f'Não foi possível consultar o Redis ({type(exc).__name__}). Revise o arquivo .env.')
        raise SystemExit(1)
