# Retomada da qualidade de motion — 06/11/2026

## Mudança posterior: um comando e avaliação final

Depois da primeira direção/cards, o titular escolheu expressamente gerar o MP4
e avaliar somente no final. Os portões intermediários descritos neste plano
ficam como histórico da proposta anterior; não bloqueiam mais este ensaio rápido.
O [comando de execução](como-executar-ensaio-motion.md) reaproveita o cenário e
encadeia as etapas, preservando orçamento, resposta e trace. A composição nova
da chamada seguinte ainda não foi gerada: o comando é verificado offline com a
v2 aprovada, sem nova API. A leitura das etapas abaixo deve considerar essa
mudança de procedimento.

## Objetivo e estado

O titular esclareceu que o ensaio pode ficar apartado de WhatsApp e Instagram,
mas precisa gerar peças reais, com entradas consistentes, referências e uso
concreto das bibliotecas. O Reel v2 é o patamar mínimo de comparação; a meta é
superá-lo. Isso é um critério de aceite humano, não uma qualidade já alcançada.
A rodada 1c permanece rejeitada. Após a preparação sem efeitos, o titular
autorizou duas chamadas até **US$ 1,50 adicionais** e o envio do pacote local
a `api.openai.com/v1/responses`. A primeira concluiu; **cinco cards foram
capturados e aguardam aceite**. A segunda chamada ainda não ocorreu e depende
desse aceite. Não há vídeo novo.

Primeiro qualificar **um Reel com o mesmo material fictício e kit**. Story e
carrossel vêm depois de comprovar esse caminho; não reaproveitar automaticamente
a mesma composição nos três formatos. A feature de vídeo continua incompleta.
Integração, normalização e CI não foram retomados nesta etapa.

## Estado após a primeira chamada

Os registros de [orçamento autorizado](../../.local/evals/motion-quality-reset-2026-11-06/round/authorization.json),
[revisão do pacote](../../.local/evals/motion-quality-reset-2026-11-06/round/payload-review.json)
e [autorização de envio](../../.local/evals/motion-quality-reset-2026-11-06/round/payload-authorization.json)
preservam as aprovações. Duas rejeições anteriores da revisão automática
ocorreram antes de iniciar o processo, sem envio ou gasto.

A operação `6bcb2d16-eff7-4cb1-b210-42db4ec9f5c9` retornou HTTP 200/completed
em **236,653 segundos**. Uso: 46.134 tokens de entrada, dos quais 46.131 de
escrita de cache e zero de leitura; 12.443 de saída, incluindo 4.789 de
raciocínio. A [estimativa de custo](../../.local/evals/motion-quality-reset-2026-11-06/round/cost-review-after-call-1.json)
é **US$ 0,2397635**, sem confirmação de fatura; a reserva de US$ 0,75 permanece.
[Saída legível](../../.local/evals/motion-quality-reset-2026-11-06/round/call-1/output.md)
e [resposta bruta](../../.local/evals/motion-quality-reset-2026-11-06/round/call-1/response.body)
foram preservadas; SHA-256 da resposta:
`e44bb830eace085603244d1e02fc4a3419662cba05dd95e8e91e5c432215b98a`.

A [folha de contato](../../.local/evals/motion-quality-reset-2026-11-06/round/call-1/static-review/contact.png)
reúne cinco cards de 720×1280 e três quadros v2. Os cards foram vistos pelo
agente e aguardam aprovação do titular; isso não comprova movimento ou áudio.
O HTML ficou intacto e não houve requisições inesperadas. A diferença de 1 px
na primeira captura foi resolvida aumentando o viewport, sem mudar a arte;
[tentativas registradas](../../.local/evals/motion-quality-reset-2026-11-06/round/call-1/static-review/attempts.json).
Nenhum MP4 novo ou segunda chamada foi produzido nesta etapa.

## Preparação concluída sem novas chamadas

- Baseline privada em `.local/evals/motion-quality-reset-2026-11-06/baseline/`:
  direção, código, gravação, áudio e resultados históricos identificados por
  hash; grades a cada 0,25 s e análise dos quatro momentos do v2. A análise de
  diferenças de pixels mistura motion gráfico com movimento da gravação e
  **não serve como nota de qualidade**. Não houve nova escuta perceptiva.
- Revisão de código real de três projetos: `cartaz-gritado` (tipografia medida,
  entrada escalonada e máscara), `cartaz-risografia` (carimbo, textura e varredura)
  e `diagrama-azul-marinho` (desenho por comprimento de caminho e pulso causal).
  São opções de mecanismo; não combinar três estilos completos nem impor
  estética fixa ao negócio. Seleção automática justificada para a peça.
- Executor privado de HTML/CSS e JavaScript revisado com relógio explícito,
  Canvas/WAAPI e até 16 eventos de áudio. A reprodução da v2 WAAPI produziu,
  nesta configuração, o mesmo SHA-256 do MP4 anterior:
  `2e9e38be97240745a7f5abbfa3dfea3962d445375f2df48575c6968bef4cb7d0`.
  Foram 336 quadros; sete amostras decodificadas coincidiram e a comparação PCM
  também coincidiu. Isso prova esta reprodução, não melhora criativa, igualdade
  entre ambientes ou prontidão de produção. Três testes locais do áudio passaram.
- Ferramentas locais conferidas pelo `checar.sh` da skill: Node, FFmpeg,
  FFprobe e Python disponíveis; nenhuma instalação.
- Cópia própria importada no repositório fornecido pelo titular:
  `../meu-braco-direito-motion-sources/snapshots/claude-video-2026-11-05/`.
  São 24 fontes originais, dois registros históricos e quatro arquivos de
  empacotamento; 30 arquivos verificados offline após a cópia. README existente
  preservado. Licenças MIT e avisos mantidos; sem mídia, fontes ou dependências
  de terceiros incorporadas. Não houve commit/push; privacidade remota e backup
  independente ainda não comprovados. Não é espelho completo da biblioteca.

## Fluxo candidato que será efetivamente avaliado

1. **Caso congelado:** mensagem simulada do Reel, kit, gravação, fatos e fontes.
   Reutilizar a interpretação Jev e a transcrição aceitas na rodada 1c, com
   identificadores, hashes e indicação expressa de reaproveitamento. Não simular
   novas chamadas nem chamar esse ensaio de integração completa.
2. **Referências concretas:** anexar quadros da gravação e da v2, perícia temporal,
   timeline aprovada, skill claude-video aplicada ao Reel e código/fichas originais dos três projetos.
   O modelo recebe imagens e texto; não recebe nem ouve um vídeo/áudio completo.
   Sons existentes são descritos e vinculados por ID, com limites da análise.
3. **Direção e cards — chamada 1:** conceito, escolha automática de uma linguagem,
   storyboard com tempos e movimentos, texto, enquadramentos e cards estáticos
   com fontes/mídia reais. Registrar quais funções concretas serão adaptadas,
   sua origem e o motivo. Não solicitar código animado nesta etapa.
4. **Revisão dos cards:** mostrar os quadros antes de construir a animação.
   A skill [claude-video](https://github.com/Felpborges/claude-video) aplicada
   contém o portão: “Nunca anime antes dos cards aprovados.” O arquivo local
   consultado foi `/Users/israelsilva/.codex/skills/claude-video/SKILL.md`.
   Esse portão não pede que o cliente escolha um estilo.
5. **Composição — chamada 2, somente após aceite:** implementar o storyboard
   aprovado com os componentes reais adaptados, HTML/CSS/Canvas/WAAPI e
   `seek(ms)`, mais plano de áudio. Preservar a resposta original; comparar
   os trechos efetivamente usados com suas fontes e registrar adaptações.
6. **Execução e revisão:** revisar o código antes de executá-lo, capturar os
   quadros-chave e seguir o outro portão da skill: “Nunca renderize o final
   antes dos frames aprovados.” Depois gerar MP4 por navegador e FFmpeg.
   Verificar legibilidade, tempos, primeiro/último quadro, mudanças de
   composição, áudio e fidelidade entre storyboard e peça; comparar com a v2.
   Falhas não autorizam refação paga automática.
7. **Entrega rastreável:** vídeo, cards, storyboard, inputs/outputs, configuração,
   uso/custo, decisões e qualquer intervenção do agente. O titular julga a
   qualidade final. Se reprovada, registrar a causa e planejar a próxima ação
   antes de ampliar formatos ou gasto.

Esta proposta recupera liberdade criativa antes de decidir quais capacidades
devem entrar no renderer parametrizado do produto. **O executor privado ainda
não é o pipeline da aplicação.** Uma aprovação futura qualifica o caminho
criativo testado; sua migração deverá preservar os mesmos inputs, componentes e
peças de regressão. Não comprimir novamente a saída para um contrato incapaz de
representá-la e apresentar o resultado alterado como equivalente.

O teste muda prompt, referências, componentes, esforço e executor em relação
à 1c. Portanto, avalia o conjunto proposto; não isola causalmente o efeito da
biblioteca. Para repetição posterior, congelar essas versões. Geração por modelo
continua não determinística; a reprodução da composição aprovada deve ser
verificável no ambiente fixado.

## Plano apresentado e posteriormente autorizado

O primeiro pedido concreto está em
`.local/evals/motion-quality-reset-2026-11-06/proposal/body-1.json`, acompanhado
de `instructions.md`, `input.md` e manifesto legíveis. SHA-256:
`6ef958be5c76b28d1a741bd44b7bb125722e8db552df5d7756f378bcbdb90cbb`.
Contém 117.491 caracteres de texto e 12 imagens (seis da gravação e seis da
referência); corpo total 2.517.385 bytes. Bytes/caracteres não são contagem
de tokens nem custo. A segunda entrada é um template ainda não enviável,
pois depende da resposta e dos cards aprovados. O rótulo técnico do kit
fictício está identificado como metadado que não pode aparecer na arte/voz.

**Autorização específica recebida, conforme registro acima.** Duas chamadas Responses
com `gpt-6.1-sol`, esforço `high`, serviço padrão e até 32.000 tokens de saída
por chamada: direção/cards e, após aceite, construção da animação. O modelo é
da mesma família usada na v2; aumentar esforço não garante qualidade. Sem novas
chamadas Jev, transcrição, imagem, TTS, música, vídeo generativo ou retry.

| Chamada | Condição | Estimativa de custo | Reserva |
| --- | --- | --- | --- |
| 1 — direção, storyboard e cards | Autorizada e concluída | US$ 0,25–0,60 planejados; US$ 0,2397635 após uso | US$ 0,75 |
| 2 — composição animada | Cards aprovados e primeira resposta utilizável | US$ 0,25–0,60 | US$ 0,75 |
| Total adicional da rodada | Sem refações automáticas | **US$ 0,50–1,20** | **US$ 1,50** |

Tarifas oficiais consultadas em 06/11/2026: entrada padrão US$ 2/milhão de tokens,
saída US$ 10/milhão; gravação de cache pode custar US$ 2,50/milhão. Estimativa
considera volume textual/imagens e tokens de raciocínio; uso real e eventual
cobrança de imagens/cache permanecem sujeitos à resposta/fatura. Fontes:
[modelo](https://developers.openai.com/api/docs/models/gpt-6.1-sol) e
[preços](https://developers.openai.com/api/docs/pricing?latest-pricing-expanded=true).
Reavaliar antes da chamada caso o pedido final exceda a premissa da reserva.

O teto operacional autorizado é **US$ 1,50 adicionais**. A rodada anterior foi
encerrada com reservas conservadoras de US$ 1,55 e estimativa de US$ 0,263073;
não há reaproveitamento de sua autorização nem redução retroativa de reservas.
Com a nova rodada autorizada, reservas planejadas acumuladas são US$ 3,05,
em dois escopos separados. O novo teto limita iniciar chamadas; não limita a
cobrança do fornecedor por uma chamada já enviada. A primeira operação teve ID,
hashes e reserva registrados antes da rede; a segunda mantém esse requisito,
sem alterar os ledgers históricos.

## Limites e próximos critérios

Cards/frames não demonstram ritmo ou áudio; o MP4 final e o julgamento do titular
continuam necessários. O código do modelo exige revisão antes de execução.
Sandbox do Chromium, allowlist e CSP foram exercitados na fixture conhecida,
mas não comprovam isolamento de rede no sistema operacional; isolamento adequado
para uma cena nova deve ser resolvido antes de executá-la. Não receber conteúdo
real de cliente nesta prova. Dependências ainda não estão empacotadas para produção.

Usar fontes autorizadas já disponíveis e preservar licenças das adaptações.
Os originais consultados usam GSAP/CDN; a proposta adapta funções de desenho para
o relógio local, sem executar ou distribuir automaticamente essas dependências.
Os outros projetos pesquisados permanecem disponíveis como candidatos, sem
afirmar que todos foram adotados ou usados neste teste.

Somente após aceite criativo: qualificar story, depois carrossel, e então
retomar a integração que entrega prévia, ajustes, aprovação e download.
WhatsApp/Instagram não são requisitos desta prova de qualidade. O último CI
integral aprovado permanece o baseline de 5.044 testes Python e 62 Node; o CI
posterior da clareza de contrato foi interrompido por pedido do titular, com
saída 143, sem resultado final. Não se executou CI nesta preparação privada.
