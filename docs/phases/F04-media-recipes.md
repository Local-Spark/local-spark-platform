# F04 — Artes, carrosséis e edição de vídeo

Atualizado em **28/10/2026**. Estado: renderers técnicos, revisões e candidata
simulada locais; geração visual real e receitas comerciais pendentes.
Dependências: F02/F03. A prioridade corrente é [BL04](BL04-context-and-ai-production.md)
seguida de BL05; o [SDD geral](../SDD.md) e as [decisões](../DECISIONS.md)
prevalecem sobre premissas antigas. A [versão anterior integral](../history/2026-10-28-pre-documentation-reconciliation/phases/F04-media-recipes.md)
preserva as fatias F04.1–F04.3, benchmarks, comandos e contagens datados.

## Jornada e direitos

O cliente acompanha/revisa em **Conteúdos** (`/app/content`); `/app/ideas`
redireciona para lá. Pedidos manuais de render e controles técnicos ficam em
`/app/editorial-lab`, só no build DEV. O percurso principal pretende entregar
candidata pelo WhatsApp; hoje a entrega correspondente é simulada e durável.
Aceitar roteiro ou solicitar prévia não aprova publicação.

O aceite único em **Plano e acesso** cobre IA de texto, imagem, interpretação
e transcrição. Não reintroduzir toggles por fornecedor. Configuração técnica,
plano, orçamento, membership, fontes e direitos continuam gates internos.
Registros legados são compatibilidade; aceite não os reescreve ou revive pedidos
antigos. A aprovação final liga peça/hash, legenda, destino e horário na F06.

BL01 é vitrine fictícia pré-produzida, sem gerar a cada visita. BL02 já entrega
seleção/edição do kit; BL03.1/BL03.2 entregam acervo privado opcional. F03 congela
o kit exato e o briefing experimental pode recuperar itens/fotos pertinentes.
A simulação BL04 aplica o kit; a produção visual real ainda não está conectada.
A galeria inteira não acompanha a chamada: uma referência pertinente do kit,
quando necessária, e referências reais do negócio são entradas distintas.

## F04.1/F04.1b — imagem técnica implementada

- `POST/GET /media-previews`, sob o prefixo autenticado por negócio, exige owner
  e acesso aplicável. O caminho manual recebe `operation_id` e proposta com
  roteiro concluído/aceito; a candidata automática tem contrato próprio, abaixo.
  Foto/feed JPEG 1080×1350 ou story 1080×1920 usam fato vigente literal e foto
  opcional do mesmo negócio. O template Pillow v4 é baseline técnico, sem selo
  de receita comercial.
- `render_key` fixa documento/versão do roteiro, contexto, marca, hash de fonte
  e versão do renderer. Operação única, lease/fencing, tentativas limitadas e
  workflow Temporal impedem duplicação local. Revalidar entradas após upload
  antes de `completed`; não fazer storage/HTTP enquanto se mantém row lock.
- O template v4 preserva foto inteira em vários enquadramentos, fundo desfocado
  separado, painel factual opaco e contraste calculado. Arte sem foto é composição
  identificável, sem fingir ser fotografia de um produto real. Preço/texto factual
  vêm literalmente da fonte confirmada.
- Ajuste `parent_preview_id` e `emphasis=photo|text|balanced` cria arquivo privado
  imutável, com operação/CAS, versão e chave distintas. Limite de quatro versões;
  pai deve ser o último válido. Não altera fato ou roteiro por essa via.
- `GET /{preview_id}/download-link` exige autorização e revalida estado/fonte.
  Arquivo privado e URL assinada curta são distintos de retenção do arquivo.
  A política atual ainda aplica prazos de proposta/prévia e limpeza pelo
  reconciliador; a mudança aprovada de preservação está pendente, abaixo.

O corpus `static-art-ptbr-v1.json`, `scripts/evaluate_static_art.py`, o cabeçalho
`static-art-human-review-template.csv` e `scripts/score_static_art_reviews.py`
permitem benchmark técnico e revisão privada. Exemplos/evals não são materiais
homologados de clientes. Não usar silenciosamente o template como substituto de
uma saída generativa ruim.

## F04.2/F04.2b — vídeo técnico implementado

Roteiro `short_video` usa os mesmos controles de fonte, hash, operação, storage
privado e Temporal. FFmpeg produz MP4 H.264 vertical 1080×1920, aproximadamente
oito segundos, com foto/clipe autorizado ou cartões. O template v4 preserva quadro
inteiro sobre fundo desfocado, usa abertura/CTA do roteiro e fato literal; em clipe
suficiente, usa dois trechos temporais distintos. Essa escolha não é semântica.

A saída é **silenciosa**, sem voz, música ou legenda alinhada à fala. Texto de
cena não deve ser anunciado como transcrição sincronizada. Fonte limitada a
5 MiB de foto/50 MiB de vídeo e saída a 20 MiB; processo FFmpeg de até 90 segundos,
dois threads e worker isolado. Ajustes de ritmo versionados preservam fonte/fato:
equilibrado 2/4/2 s, mais cena 3/3/2 s, mais leitura 1/5/2 s; até três revisões.

`scripts/evaluate_video.py`, corpus `video-ptbr-v1.json`, cabeçalho de revisão e
`scripts/score_video_reviews.py` exercitam o baseline. Render real FFmpeg com
mídia sintética foi validado; não chama Meta/OpenAI. Seleção relevante de trechos,
áudio/legenda, qualidade em celular e COGS staging continuam pendentes.
Vídeo e sua franquia não estão automaticamente incluídos na hipótese inicial de
R$ 99 com foto/feed e story. Motion, HyperFrames/Remotion e motores de edição
avaliados são candidatos; não constituem integração entregue.

## F04.3 — candidata e entrega simulada implementadas

O workflow filho de material processado pode pedir proposta, aguardar roteiro,
criar `candidate=true` e registrar entrega simulada por evento (`0035`/`0036`).
Não exige aceite manual do roteiro para iniciar essa candidata, sem alterar seu
`review_state`. Sem fato/fonte suficiente, registra esclarecimento simulado.
Replay não duplica prévia/entrega. A simulação BL04 também pode aplicar kit,
logo e texto conferidos sobre cena neutra, com marca explícita de simulação.

Troca de número não cancela material já associado: o processo continua para o
mesmo negócio e a entrega simulada espera vínculo válido no número ativo novo.
O fluxo ainda não envia prévia/legenda/pedido de aprovação pela API oficial.
A F06 já registra decisão da peça e publicação falsa; pedido de ajustes ainda
não cria automaticamente nova versão. Comando factual `Confirmar` da F02 não
aprova publicação.

## Mudanças aprovadas e próximas integrações

**Implementação parcial:** no modo visual simulado, mudança de contexto/catálogo,
confirmação de kit e fotos do acervo pode aguardar trabalhos admitidos; bloqueia
novas admissões e cancela fila não iniciada. Prévia concluída antes da alteração
permanece revisável e identificada. Outros escritores e transições de acesso
não têm coordenação completa. Upload incerto pode ser descartado pelo autor após
lease; quarentena não tem limpeza física automática.

**Aprovado, ainda não implementado:** se o plano vencer durante criação já
iniciada, concluir e permitir revisão privada; bloquear nova criação/publicação
até renovar. Preservar prévias geradas sem expiração automática enquanto a conta
estiver ativa. O código atual ainda possui `expires_at`, limpeza de propostas/
prévias e gates de plano incompatíveis com parte desse alvo. `0058` preservou
somente envios WhatsApp. Validade factual e prazo da aprovação não se prolongam
porque o arquivo foi guardado; URL assinada continua curta. Encerramento de conta
terá política própria depois, sem limpeza automática nova nesta etapa.

Recuperação de pendência cujo autor perdeu acesso será exclusiva da equipe da
plataforma, com ação registrada/auditada. Não existe ainda o fluxo de staff, e
outro owner não assume a pendência. Isso não concede acesso global à mídia privada.

**BL04.2 pendente:** implementar guarda concreta de fontes/aceite único/plano/
acesso/orçamento, comprovar concorrência com mocks e ligar dispatcher, workflow
separado e provedor. Adapter/orquestrador real existem isolados, e
`VisualEffectGuard` ainda é `Protocol`. `VisualGenerationWorkflow` tem prazos e
uma tentativa testados, mas não está registrado no worker ou ligado ao dispatcher.
O ledger já tem teto por tenant e agregado mensal OpenAI; integrar controles sem
confundir reserva estimada com fatura. Resultado incerto retém prova/reserva,
sem retry pago ou troca automática de provedor.

## Gates de qualidade e custo ainda abertos

Comparar composição por receita com geração/edição visual usando o mesmo material,
briefing e kit. Escolher por fidelidade, qualidade, aceite e custo de **todas**
as tentativas por peça aceita. Texto, preço, CTA e logo precisam estar literais;
produto/local reais devem permanecer reconhecíveis. Cena inventada exige
identificação conceitual. Foto pública não concede direitos ou aceite da titular.

Os critérios de revisão das receitas técnicas permanecem:

- Ao menos 20 peças autorizadas, quatro segmentos e avaliação em celular. Para
  vídeo, incluir no mínimo cinco fotos e cinco clipes. Registrar hash, fonte,
  segmento, consentimento e avaliador em CSV privado, sem mídia ou contato no Git.
- Pelo menos 90% com nota ≥ 4/5 de legibilidade e visibilidade do assunto; vídeo
  também avalia coerência dos cortes. Pelo menos 80% aceitas sem ajuste.
  Registrar rejeições por segmento/fonte. Erro crítico de fato, preço, direito,
  produto ou apresentação enganosa bloqueia piloto até correção/reavaliação.
- Medir p50/p95, CPU, bytes, storage, tráfego, retrabalho e custo real em staging.
  O corpus sintético não comprova custo cloud, margem ou qualidade comercial.

BL04.3 começa por post/story personalizados e revisão consentida, sem prometer
os demais formatos da fase completa. Hipótese econômica: R$ 99/mês e custo total
pretendido ≤ R$ 50 por cliente/mês, ainda sem comprovação. F05 trata identidade
sintética após o primeiro piloto; BL05 completa ajuste automático e proatividade.

Testes locais preservam RLS, replay, fencing, fonte inválida, concorrência,
arquivo parcial e incerteza sem efeito externo pago. Detalhes históricos dos
ensaios de 25–28/10 estão no snapshot e em [evals](../evals/); validação corrente
no [CHANGELOG](../CHANGELOG.md). Atualizar fase, PROJECT, SDD e CHANGELOG em cada
entrega. Mock ou adapter isolado não fecha homologação externa.
