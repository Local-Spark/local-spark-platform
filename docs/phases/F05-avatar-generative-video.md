# F05 — Avatar, voz e cenas geradas

Decisão de 26/10/2026: [plano de qualidade criativa](../design/creative-production-quality.md)
separa avatar/voz e cena generativa das receitas de foto real e vídeo editado.
Sem benchmark de consentimento, qualidade PT-BR e custo por peça aceita, nenhuma
dessas capacidades integra a franquia de R$ 99 ou a promessa do primeiro piloto.
O uso em plano superior depende dos mesmos gates e de preço medido.

Status: Planejada. Atualizado em 20/10/2026.
Dependências: F01, F03, F04.

## Objetivo

Permitir vídeos do próprio dono e composições híbridas sem nova gravação em cada publicação.

## Features e contratos

- Captura guiada, consentimento comprovado e IDs de identidade separados por fornecedor/tenant.
- owner_avatar_reel, hybrid_reel e generated_scene_reel com limites de duração/franquia.
- Submit/status/callback/polling, UNKNOWN e controles de custo antes de chamada paga.
- Revogação impede novas gerações e cancela pendentes; exclusão é operação rastreável.
- Adapters separados por capacidade de avatar, voz e cena; avaliar HeyGen, Runway,
  Kling e Veo como candidatos conforme API comercial, PT-BR, consentimento, direitos,
  custo, latência e exclusão. Nenhum primário novo é escolhido sem spike e benchmark.
  Decisão de provedor/receita é registrada antes do submit; fallback que mude
  identidade, formato ou custo exige nova aprovação.

## Critérios de aceite e testes

- Qualidade PT-BR, sotaques, preço/nome e latência/custo medidos.
- Callback duplicado/perdido e submit ambíguo não disparam gasto cego.
- Revogação concorrente e falha de compensação com suporte auditado.
- Corpus consentido avalia sotaque, sincronização, consistência de face, texto/preço
  e custo por peça; shadow eval limitado por coorte e orçamento, não contínuo para
  toda a base.

## Limites e decisões pendentes

- API, slots de identidades, licença de uso e quotas contratadas precisam de evidência.
- Fallback não muda aparência/voz do cliente silenciosamente.

## Integração e manutenção

Dividir as features acima em mudanças revisáveis. Cada mudança atualiza este SDD,
`docs/PROJECT.md` e `docs/CHANGELOG.md`, incluindo evidências de testes e pendências.
Contratos que afetam outras fases devem ser refletidos no SDD geral e nos consumidores.
Não marcar como concluído por possuir mocks ou documentação de uma API ainda não validada.

## Consentimento e interfaces

Autorização de voz/avatar usa página curta complementar e registro específico;
termos do onboarding não autorizam identidade sintética. Cliente vê estado da
geração; admin acompanha custo e falha, com acesso mínimo e auditado.
