# Plano de execução — reels 15s de fotos (qualidade), 17/11/2026

## 17/11/2026 — lab: construção automática, aprovação somente da peça pronta

Por solicitação explícita do titular, esta decisão substitui Q5b/A2: novos reels
do lab não exigem aprovação intermediária de plano, render ou storyboard. Fotos
usam planned_photo_request(human_review=False), como WhatsApp: planejamento e
validação automáticos antes de implementar. Vídeos seguem o caminho produtivo
automático, inclusive em drafts antigos ainda não iniciados. Não são emitidos
eventos fictícios de aprovação. Aprovação final approve-piece, RLS, Music,
reservas, revisão e integridade permanecem; nenhuma geração paga nesta mudança.

Frontend remove a galeria de frames e seus downloads. Checkpoints legados e
perguntas de outros formatos permanecem compatíveis. Runs já iniciados conservam
snapshot/contrato original: não foram migrados, retomados ou cobrados. Para usar
o novo comportamento, reiniciar API/worker e iniciar um novo reel. Frames
internos de revisão automática continuam necessários e não são aprovação humana.

Validação: 15 testes unitários (planejamento photo e snapshots de vídeo) e três
de integração photo lab/WhatsApp passaram no banco dedicado _test. TypeScript
do frontend e Ruff da fatia passaram. Make ci bloqueado no lint global com 66
ocorrências. Aceite UI/MP4 e cobertura global permanecem pendentes.


## Atualização A2 — 17/11/2026 (escopo confirmado pelo titular)

Implementação limitada a A2: planejamento photo no fluxo compartilhado,
relações `photo_dominant`/`integrated` com materiais autorizados, checkpoint de
plano obrigatório no lab e validação/implementação automática no WhatsApp.
Reserva considera implementação, revisão e correções configuradas. Music A1
preservada; flag local habilitada por autorização expressa, sem alterar tetos.
Testes adicionados, mas execução adiada expressamente pelo titular para etapa
posterior. Sem aceite novo de ponta a ponta ou chamada paga. Detalhes no topo
de PROJECT/SDD/BL04/CHANGELOG. A3–A5/N continuam fora desta mudança; a menção
anterior a concluir todas as fatias foi substituída pelo pedido explícito A2.


## Atualização de execução A1 — 17/11/2026

O pedido posterior autorizou **código e testes de A1**, sem autorizar chamada
paga ou ativação. Implementados adapter Music, cache criptografado por negócio,
reserva mensal por tenant e vínculo durável de trilha à operação; mix e retomadas
usam a mesma trilha. Flags e limites ficam desativados por padrão. Testes usam
somente áudio sintético/fake; a prova de MP4 decodificado passou, escuta real
continua pendente. Gates globais de CI continuam pendentes; detalhes e limites
no topo de PROJECT/SDD/BL04/CHANGELOG. Os registros de aprovação abaixo são
históricos e não autorizam novas despesas. A2–A5/N não foram implementadas.


Estado: **plano documentado e decisões da entrevista registradas**.
Não autoriza, por si só, implementação de A1–A5, download de música, chamada
paga, TTS nem execução automática de testes. A0 nesta versão é **somente
checklist manual documentado**, sem código novo.

Decisões do titular (entrevista 17/11/2026):

| Id | Escolha | Significado |
| --- | --- | --- |
| Q1 | a | Registrar o plano em docs; **não** executar A0 operacional neste ato |
| Q2 | c | A0 = checklist manual documentado (sem script/comando novo) |
| Q3 | a | Candidatos Freesound apresentados; titular rejeitou qualidade para jazz café |
| Q3b | 17/11 | Trilha photo reel → **ElevenLabs Music** (gerar + cache interno); SFX → Freesound CC0 |
| Q4 | a | Silêncio se o usuário pedir ou não houver faixa elegível |
| Q5 | b | Lab: checkpoint de plano sempre; WhatsApp: validação automática → implementa |
| Q6 | b | Narração inventada (TTS) entra como **fatia extra** (não nesta onda visual-only) |
| Q7 | b | Primeira prova OpenAI pós-A0: teto ≤ US$ 5 |

Referências de método e gap: análise Maestros
[WuzMxEKJHkQ](../evals/analise-video-maestros-WuzMxEKJHkQ-2026-11-11.md);
peça `versao-1.mp4` (15s, sem áudio, holds longos, dois cortes). Consenso com
revisão externa incorporado (confiabilidade, staging foto sem gambiarra,
integridade vs estética, caminho compartilhado, aprovações distintas, custo).

## Objetivo e fora de escopo desta onda

Melhorar o piso de reels curtos feitos a partir de fotos autorizadas (lab +
WhatsApp no serviço compartilhado): trilha, planejamento photo-compatible,
intenção visual/tipográfica, métricas e, em fatia própria, narração TTS.

Fora desta onda (salvo fatia N quando autorizada): avatar/HeyGen, GSAP/Remotion,
ElevenLabs **Voice**/clonagem (distinta de Music), auto-aumento de orçamento,
Marketplace ElevenLabs como UX de escolha do cliente, gates estéticos rígidos
antes da calibração.

## O que melhora (mapa)

| Problema | Onde | Fatia |
| --- | --- | --- |
| MP4 sem áudio em photo reel | `photo_music` / manifesto só SFX | A1 (ElevenLabs Music + cache) |
| Lab v2 single-shot “post estático” | `MotionRequest` mínimo | A2 |
| Staging foto rejeita relações sem `video` | `motion_staging` L67 | A2 |
| Checklist de efeitos ≠ qualidade | skill/review | A3 |
| Review “adequate” em peça morta | métricas | A4 |
| Config/renderer quebram no ensaio pago | readiness incompleto | A0 |
| Sem fala em photo reel | política atual anti-fala inventada | N (TTS) |

## Princípios

1. Regras no serviço compartilhado; lab avalia (com checkpoint de plano).
2. Provedor pago só com teto explícito, depois de A0 checklist ok.
3. Integridade bloqueia já; estética informa até calibrar.
4. Texto na tela pode ser editorial; **narração TTS** é fatia N (autorizada na
   entrevista como direção), distinta de fingir transcrição de gravação.
5. Correções → contrato/repertório versionado, não adjetivo na skill.
6. Sem ampliar orçamento automaticamente.

## Aprovações

| Decisão | Quem | Lab (Q5b) | WhatsApp (Q5b) |
| --- | --- | --- | --- |
| Validação automática do plano | Serviço | Sempre (pré-checkpoint) | Autoriza implementação |
| Aprovação criativa do plano | Humano | **Sempre** (`review_checkpoints` / plano) | Não (modo automático) |
| Aprovação final da peça | Humano | UI / conteúdo | UI / conteúdo |

Não fingir `motion.plan_approved` no automático. No lab, retirar o clique não
está autorizado por Q5b.

## Custo

Planejamento aumenta etapas. Se a reserva não comportar implementação, revisão
ou correção: erro estável, sem subir teto sozinho. Aceite humano registra custo
acumulado. Primeira geração paga autorizável após A0: ≤ US$ 5 (Q7b), ainda
sujeita a OK explícito na hora.

## Fatias

### A0 — Checklist manual de confiabilidade (sem código novo)

**Comprova:** que a configuração local e o ambiente parecem aptos a um ensaio
posterior. **Não comprova:** qualidade criativa, compatibilidade da resposta
OpenAI, nem “percurso sintético completo” automatizado (Q2c exclui script/job
novo nesta fatia).

**Começa / termina:** preenchimento do checklist abaixo com evidências (comandos
de leitura, PIDs, digests, erros). Sem alteração de repositório além deste plano
e dos registros centrais que apontam para ele.

#### Configuração (anotar pass/fail e evidência)

- [ ] `motion_execution_enabled` e `motion_ai_mode` conforme intenção do ensaio
- [ ] Tarifa de entrada/saída passa na política interna (`validate_tariff`)
- [ ] Reserva e orçamento de requisição coerentes; orçamento lab/mensal conforme uso
- [ ] Credenciais OpenAI presentes **somente** se o próximo ensaio for pago
- [ ] `motion_renderer_image` e digest conhecidos; imagem local existe no Docker
- [ ] Capacidades do runner (ex.: fingerprints) compatíveis com o adapter atual
      — “imagem existe” não basta (histórico MOTION_RENDER_INVALID_OUTPUT)
- [ ] Worker do lab com poller de workflow e atividade; fila sem backlog órfão
- [ ] Correlator / crypto / storage material configurados para motion
- [ ] Contrato de staging: schema enviado alinhado ao que o serviço aceita
      (histórico MOTION_STAGING_UNEXPECTED)

#### Integridade (sem música ainda)

- [ ] Nenhum pedido queued/running inesperado antes de novo ensaio
- [ ] Último render conhecido (se houver) com duração/identidade coerentes
- [ ] Sem ampliar orçamento “para ver se passa”

#### Limite explícito

Este A0 **não** inclui job sintético automatizado com fixture + renderer.
Se no futuro quiserem essa prova (recomendação da revisão externa), será uma
fatia A0b autorizada à parte, com escopo de componentes reais vs simulados.

**Aceite A0:** checklist preenchido e arquivado (trace/nota local ou apêndice);
falhas nomeadas por bloco. Não autoriza A1 sozinho — A1 exige conta ElevenLabs
pronta (credencial + plano comercial) e OK explícito para a primeira geração.

### A1 — ElevenLabs Music + cache interno + áudio no resultado

**Decisão (17/11):** trilha de photo reel via **ElevenLabs Music**, não Freesound.
Freesound CC0 permanece para **SFX** (A5a). Ver `docs/DECISIONS.md`.

**Modelo (cliente não escolhe faixa):**
1. O sistema infere clima/mood do pedido e do negócio.
2. Busca no **cache interno** (faixas já geradas, com metadados/hash) uma
   candidata adequada; reusa bytes sem nova chamada paga.
3. Se não houver match: **gera** via API (instrumental; duração ≥15s, tipicamente
   15–30s), escuta/aceite operacional, persiste no cache e usa no mix.
4. Silêncio se o usuário pedir ou se orçamento/credencial/plano não permitirem
   (Q4a + falha clara).
5. Cliente **não vê** catálogo nem escolhe stock; não é Music Marketplace UX.

**Onde (quando implementar):** adapter ElevenLabs Music, ledger/orçamento,
armazenamento material ou biblioteca versionada de trilhas autorizadas,
`motion_photos` / `authorized_soundtrack`, testes, tarifa/reserva explícitas.
Variável prevista (local, não commitada): `MEU_BRACO_DIREITO_ELEVENLABS_API_KEY`.

**Custo:** ~US$ 0,15/min gerado (lista API); cobrança por geração. Cache evita
repagamento do mesmo arquivo. Teto por ensaio e mensal obrigatórios antes de
ligar em produção.

**Legal (resumo):** não expor outputs como biblioteca para terceiros
escolherem/baixarem. Cache operacional interno do produto. Confirmar plano
Starter+ e Music Terms vigentes antes da 1ª chamada paga.

**Aceite:** áudio **decodificado** do MP4 (duração, fades, clipping, escuta);
música autorizada ausente/vazia → falha. Prova inicial com teto explícito
(alinhado a Q7b ≤ US$ 5 para a rodada, ou subteto só de Music).

### A2 — Planejamento photo no serviço compartilhado

**Onde:** staging/schemas, context, construction, lab requests, WhatsApp /
`message_creation`, instruções, testes.

**Semântica:** definir relações visuais para **fotografias** (não classificar
toda foto como `graphic` só para passar o validador que hoje exige `video` se
`media_relation != "graphic"`).

**Modos (Q5b):** lab com checkpoint de plano obrigatório; WhatsApp com validação
automática do plano e implementação sem clique de plano.

**Custo:** falta de reserva → para; sem auto-upgrade.

### A3 — Implementação visual + tipografia pela intenção

Progressão perceptível, leitura, handoffs justificados. Sem exigir efeitos
específicos no código. Sugestões de beats/CTA = orientação, não lei.

### A4 — Métricas informativas + integridade dura

Bloquear: arquivo/duração inválidos, material não autorizado, contrato/orçamento,
(e com A1) música autorizada ausente. Informativo até calibrar: quantidade de
movimento, % quase-estático, variedade de transições, “força narrativa”.

### A5a — SFX opcionais (fatia independente)

SFX só com justificativa no plano; nunca substituto de música.

### A5b — Gates estéticos (depois da calibração)

Só com amostra humana e OK de limiares.

### N — Narração TTS para photo reel (fatia extra, Q6b)

Direção do titular: permitir narração inventada sem gravação de entrada.

**Ainda aberto antes de implementar N (não bloqueia A0–A3):**

- Provedor: ElevenLabs (pago, alinhado à referência Maestros) vs alternativa
  local/configurada; credenciais e orçamento explícitos.
- Contrato: roteiro curto ≠ “transcrição” de vídeo inexistente; tempos para
  tipografia/legendas; mix com trilha (ducking).
- Relação com F05 (avatar): N é voz apenas, sem labial/HeyGen nesta fatia.
- Lab vs WhatsApp: mesmo serviço; lab pode checkpointar roteiro se desejado.

**Ordem sugerida para N:** depois de A1 (trilha) e A2 (plano), para o plano
poder declarar falas e o mixer já ter música. Não misturar N com A0.

## Ordem de execução autorizável

```
A0 checklist (manual) → OK titular
  → pesquisa candidatos música (Q3a) → OK titular
  → A1 implementação
  → A2 planejamento photo + modos lab/WA
  → A3 intenção visual
  → A4 métricas
  → A5a / A5b conforme necessidade
  → N (TTS) após decisões de provedor/orçamento
```

Primeira prova paga OpenAI: teto ≤ US$ 5, OK explícito na hora, preferencialmente
após A0 (e idealmente com A1 ou baseline documentado).

Aceite humano inicial (após A1–A3 no mínimo): três ensaios — calmo, energético,
poucas fotos — mensagens/materiais/critérios preservados; custo acumulado;
não comprova qualidade consistente do produto.

## Apêndice — Checklist A0 (cópia para preenchimento)

Data: __________  Ambiente: __________  Operador: __________

| Bloco | Item | Pass/Fail | Evidência |
| --- | --- | --- | --- |
| Config | flags motion / modo AI | | |
| Config | tarifa / reservas | | |
| Config | renderer image + digest + capacidades | | |
| Config | worker lab pollers | | |
| Config | correlator / crypto / storage | | |
| Config | alinhamento staging schema↔serviço | | |
| Integridade | fila limpa / sem órfãos | | |
| Limite | sem chamada paga neste A0 | | |

Conclusão A0: apto para próxima fatia? Sim / Não — bloqueios: __________
