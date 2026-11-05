"""Testes locais sem bancos externos. Execute: python -m unittest -v testes_basicos.py"""
import os
import unittest
from pathlib import Path

os.environ['DEMO_MODE'] = 'true'
from app import app, demo_products


class TestesVexa(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_catalogo_tem_14_produtos(self):
        r = self.client.get('/api/products')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.get_json()['produtos']), 14)

    def test_todos_produtos_tem_descricao_foto_e_nome(self):
        for item in demo_products():
            self.assertTrue(item['descricao'].strip())
            self.assertTrue(item['nome'].strip())
            self.assertTrue((Path(app.root_path) / 'static/img/produtos' / item['imagem']).is_file())

    def test_detalhes_produto(self):
        r = self.client.get('/api/products/VEX-001')
        self.assertEqual(r.status_code, 200)
        self.assertIn('descricao', r.get_json()['produto'])

    def test_admin_sem_login_nao_cadastra(self):
        r = self.client.post('/api/admin/products', data={'nome': 'Teste'})
        self.assertEqual(r.status_code, 401)

    def test_status_deixa_claro_modo_demo(self):
        r = self.client.get('/api/status')
        self.assertEqual(r.get_json()['modo'], 'demonstracao')

    def test_carrinho_vazio_nao_finaliza(self):
        r = self.client.post('/api/checkout', json={'itens': []})
        self.assertEqual(r.status_code, 400)


if __name__ == '__main__':
    unittest.main()
