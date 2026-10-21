# F06 — Aprovação, agenda e Instagram

Status: Planejada. Atualizado em 20/10/2026.
Dependências: F01, F04, F05.

## Objetivo

Publicar versões efetivamente aprovadas em contas profissionais elegíveis, com rastreabilidade por destino.

## Features e contratos

- OAuth, scopes e capability discovery por conta; não pedir senha do Instagram.
- Aprovação vincula ator, versão, hashes, legenda, conta, janela e consentimento.
- Imagem/carrossel/Reel/Story elegível, processamento de container e confirmação.
- Agendamento, cancelamento concorrente, reauth e reconciliação de publicação UNKNOWN.

## Critérios de aceite e testes

- Smoke real por formato elegível e app review para usuários externos.
- Revisão não herda aprovação; cancelamento/expiração antes do envio respeitados.
- Timeout após possível publicação não cria segunda postagem automaticamente.

## Limites e decisões pendentes

- TikTok/Facebook/Shorts são expansão posterior.
- Não prometer remoção/rollback de post se API não suportar.

## Integração e manutenção

Dividir as features acima em mudanças revisáveis. Cada mudança atualiza este SDD,
`docs/PROJECT.md` e `docs/CHANGELOG.md`, incluindo evidências de testes e pendências.
Contratos que afetam outras fases devem ser refletidos no SDD geral e nos consumidores.
Não marcar como concluído por possuir mocks ou documentação de uma API ainda não validada.

## Painéis e base de métricas

Conexão OAuth e revisão da versão/destino usam páginas do cliente. Publicações
registram IDs externos e origem; iniciar coleta periódica de insights autorizados
com snapshots, período e última sincronização conforme políticas da plataforma.
Admin acompanha operação. F07 agrega e apresenta evolução; indisponível não vira zero.
