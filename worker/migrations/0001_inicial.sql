-- Arquivos do app guardados como texto, exatamente os bytes recebidos (UTF-8).
-- chave: "app/versao.json"
CREATE TABLE arquivos (
  chave         TEXT PRIMARY KEY,
  conteudo      TEXT NOT NULL,
  etag          TEXT NOT NULL,   -- SHA-256 do conteúdo (resposta condicional, 304)
  atualizado_em TEXT NOT NULL
);
