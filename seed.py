"""Importa / atualiza os 14 produtos de demonstração no MongoDB real."""
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env')
uri = os.getenv('MONGODB_URI', '')
if not uri or 'SEUCLUSTER' in uri:
    raise SystemExit('Configure uma MONGODB_URI válida no arquivo .env primeiro.')
items = json.loads((ROOT / 'data/produtos_demo.json').read_text(encoding='utf-8'))
atualizar_descricoes = '--atualizar-descricoes' in sys.argv
client = MongoClient(uri, serverSelectionTimeoutMS=5000)
col = client[os.getenv('MONGODB_DB', 'vexa_store')]['produtos']
col.create_index('sku', unique=True)
count = 0
for p in items:
    operacao = {'$setOnInsert': p.copy()}
    if atualizar_descricoes:
        operacao['$set'] = {'descricao': p['descricao']}
        del operacao['$setOnInsert']['descricao']
    col.update_one({'sku': p['sku']}, operacao, upsert=True)
    count += 1
print(f'{count} produtos verificados/importados no MongoDB. Sem duplicar SKUs existentes.')
if atualizar_descricoes:
    print('Descrições dos 14 SKUs também foram atualizadas; nomes e preços existentes foram preservados.')
