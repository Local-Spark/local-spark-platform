# F02 — WhatsApp e biblioteca de materiais

Status: Em implementação; F02.1 ingressão segura entregue localmente em 21/10/2026.
Dependências: F00, F01.

## Objetivo

Receber texto, áudio, fotos e vídeo no número oficial da plataforma e montar solicitações com fatos rastreáveis.

## Features e contratos

- Handshake/assinatura Meta, inbox, subeventos, recibos e deduplicação por adapter.
- Download autorizado, inspeção de mídia, biblioteca S3 privada e agrupamento de mensagens.
- Extrair áudio, transcrever e identificar ambiguidades de preço/data; perguntar o necessário.
- Anexos são dados não confiáveis; limites, SSRF e sandbox de mídia implementados.
- Capturar de modo opcional tom, produtos/serviços, ofertas, restrições e frequência
  informados pelo dono, com ator, mensagem-fonte, data e consentimento. Guardar como
  propostas de contexto; transcrição ou inferência ambígua pede confirmação e não
  valida preço, horário ou promoção. Não aumentar o formulário obrigatório da F01.

## Critérios de aceite e testes

- Webhook duplicado/parcial/reordenado, callback antes da correlação, arquivo inválido e expiração de URL.
- Agrupamento concorrente e contexto de duas empresas sem mistura.
- Mensagem bruta e instrução embutida não alteram preferências/fatos confirmados sem
  identidade, confirmação e operação idempotente.
- Smoke com WhatsApp oficial e material consentido.

## Limites e decisões pendentes

- App/WABA, número e templates precisam de configuração e validação.
- A caixa de entrada do produto não equivale às conversas de vendas do cliente.

## F02.1 — Webhook autenticado e inbox isolada (entregue localmente)

`GET /api/v1/webhooks/whatsapp` devolve o desafio apenas com modo `subscribe` e
verify token correto. `POST` limita o corpo a 256 KiB durante a leitura, valida
`X-Hub-Signature-256` sobre os bytes originais com o App Secret, exige envelope
WhatsApp e filtra WABA/phone number ID configurados. Separa mensagens recebidas e
transições de status; chave estável por subevento deduplica reentregas concorrentes.
Só retorna 200 depois do commit. Eventos ficam cifrados com chave exclusiva em
`whatsapp_inbox`, com RLS/role `local_spark_meta` e login isolado. Runtime normal
não possui leitura. Eventos não reconhecidos são ignorados sem criar negócio ou
tratar texto externo como comando. Registros vencem em sete dias; ingressão nova
remove os vencidos, e limpeza periódica fica para F02.2. Configuração desabilitada
responde 503, sem simular uma conexão Meta.

Não existe ainda vínculo de remetente WhatsApp ao tenant: o SMS de F01 comprova
posse do número cadastrado, mas não autoriza associar qualquer mensagem recebida
na caixa central a esse negócio. Portanto os eventos permanecem em quarentena e
**não** iniciam Temporal, download, transcrição, resposta nem publicação. F02.2
implementa prova de vínculo do canal, resolução segura de tenant/negócio, retenção
periódica, material no S3 privado e outbox/workflow. Status de mensagens de saída
sem correlação também aguarda essa fatia. Smoke real exige App/WABA e número da Meta.

Aceite local: desafio válido/inválido, assinatura ausente/incorreta, payload parcial,
subeventos ignorados, reentrega concorrente, criptografia, separação de roles,
readiness e rollback/upgrade de migration 0013 no banco `_test`. 271 testes,
100% de linhas/ramos, Ruff e mypy aprovados. Nenhum evento real da Meta foi testado.

## Integração e manutenção

Dividir as features acima em mudanças revisáveis. Cada mudança atualiza este SDD,
`docs/PROJECT.md` e `docs/CHANGELOG.md`, incluindo evidências de testes e pendências.
Contratos que afetam outras fases devem ser refletidos no SDD geral e nos consumidores.
Não marcar como concluído por possuir mocks ou documentação de uma API ainda não validada.

## Integração com onboarding e interfaces

A identidade é iniciada na web; a posse do WhatsApp é verificada nesta fase, antes
de associar mensagens à contratação/organização. Telefone digitado no checkout ou
perfil não é verificação. Onboarding conversacional complementa o perfil inicial,
sem exigir uso diário do painel. Consentimentos são específicos por finalidade.
