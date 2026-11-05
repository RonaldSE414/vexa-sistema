
-- VEXA STORE - BANCO DE DADOS SUPABASE
-- Tabelas de clientes e pedidos

CREATE TABLE IF NOT EXISTS public.vexa_clientes (
    id UUID PRIMARY KEY
        REFERENCES auth.users(id) ON DELETE CASCADE,
    nome TEXT NOT NULL DEFAULT '',
    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.vexa_pedidos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id UUID NOT NULL
        REFERENCES auth.users(id) ON DELETE CASCADE,
    itens JSONB NOT NULL,
    total_centavos INTEGER NOT NULL
        CHECK (total_centavos >= 0),
    status TEXT NOT NULL DEFAULT 'preparado'
        CHECK (status = 'preparado'),
    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- INDICE PARA CONSULTA DE PEDIDOS

CREATE INDEX IF NOT EXISTS vexa_pedidos_cliente_data_idx
ON public.vexa_pedidos(cliente_id, criado_em DESC);

-- SEGURANCA DAS TABELAS

ALTER TABLE public.vexa_clientes
ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.vexa_pedidos
ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON public.vexa_clientes
FROM anon, authenticated;

REVOKE ALL ON public.vexa_pedidos
FROM anon, authenticated;

GRANT SELECT, INSERT, UPDATE
ON public.vexa_clientes TO authenticated;

GRANT SELECT, INSERT
ON public.vexa_pedidos TO authenticated;

-- POLITICAS DE ACESSO DOS CLIENTES

DROP POLICY IF EXISTS vexa_cliente_ler
ON public.vexa_clientes;

CREATE POLICY vexa_cliente_ler
ON public.vexa_clientes
FOR SELECT TO authenticated
USING ((SELECT auth.uid()) = id);

DROP POLICY IF EXISTS vexa_cliente_criar
ON public.vexa_clientes;

CREATE POLICY vexa_cliente_criar
ON public.vexa_clientes
FOR INSERT TO authenticated
WITH CHECK ((SELECT auth.uid()) = id);

DROP POLICY IF EXISTS vexa_cliente_editar
ON public.vexa_clientes;

CREATE POLICY vexa_cliente_editar
ON public.vexa_clientes
FOR UPDATE TO authenticated
USING ((SELECT auth.uid()) = id)
WITH CHECK ((SELECT auth.uid()) = id);

-- POLITICAS DE ACESSO DOS PEDIDOS

DROP POLICY IF EXISTS vexa_pedido_ler
ON public.vexa_pedidos;

CREATE POLICY vexa_pedido_ler
ON public.vexa_pedidos
FOR SELECT TO authenticated
USING ((SELECT auth.uid()) = cliente_id);

DROP POLICY IF EXISTS vexa_pedido_criar
ON public.vexa_pedidos;

CREATE POLICY vexa_pedido_criar
ON public.vexa_pedidos
FOR INSERT TO authenticated
WITH CHECK ((SELECT auth.uid()) = cliente_id);
