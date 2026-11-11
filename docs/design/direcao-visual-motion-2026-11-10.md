# Direção fornecida antes da construção — etapa 3

**Retorno posterior do titular:** a proposta de planos/tipografia abaixo mostrou
melhora limitada e restringiu indevidamente os desenhos desejados. Ela permanece
histórica; a próxima prova usa a
[direção de interação entre mensagem e elementos](motion-interacao-mensagem-2026-11-10.md).
Não alterar snapshots antigos para substituir a direção.

O pedido existente aceita `scene_direction` opcional, no formato
`scene-direction-v1`. O documento contém a ideia por momento, composição,
ação, atenção e materiais. Não contém HTML, JavaScript ou outra timeline.
Tempos, curvas, relações e transições continuam em `motion_plan`, construído
depois com base na duração e nos materiais reais.

## Dois modos explícitos

- **Fornecida:** o pedido contém a direção. O snapshot usa `reel-creative-v5`,
  preserva o documento e orienta a construção. O payload identifica origem e
  hash da direção, com `human_approval=not_asserted`. A resposta deve manter o
  documento; a validação de serviço rejeita substituição antes de imagens/render.
- **Sugerida pelo modelo:** o pedido não contém direção. Mantém o fluxo existente,
  com `reel-creative-v4` para novos pedidos desse modo. O payload informa que a
  direção será proposta junto da construção, sem alegar planejamento separado.

Não foi criado um planejador automático, outra chamada, tabela de aprovação,
fila ou mecanismo de revisão por cena. Se uma correção exigir mudar uma direção
fornecida, ela precisa de nova entrada explícita, com nova operação. Não se altera
silenciosamente a decisão para satisfazer a crítica. A implementação pode escolher
dimensões finas, tempos, curvas e código coerentes com a direção e o kit.

O aceite dos quadros continua no fluxo de storyboard existente. Fornecer uma
direção ou aprovar a próxima etapa de implementação não aprova quadros ou vídeo.
Snapshots e solicitações antigos omitem o novo campo e permanecem compatíveis.

## Proposta revisável para a prova Café Pausa

[Direção em JSON](../evals/direcao-cafe-pausa-2026-11-10.json), preparada com o
mesmo schema aceito pelo produto, **ainda não aprovada criativamente pelo titular**.
Base: kit Café Pausa já confirmado e três das seis amostras originais disponíveis
(0, 4.470 e 8.940 ms) da gravação anterior. O vídeo tem 11.176 ms; o perfil de saída
anterior arredonda para 11.200 ms. Sem nova extração, escuta ou geração de mídia.

Ideia: **abrir espaço para uma pausa**. O gesto real permanece protagonista.
Planos e tipografia abrem espaço e depois transformam esse espaço em convite.
Dois momentos nesta proposta — preparo e convite — são uma escolha específica,
não uma regra do produto. A proposta não exige jarra, xícara ou vapor desenhados.
Não são criadas afirmações sobre ingredientes, preço, qualidade ou localização.

| Momento | Relação entre mensagem, gravação e movimento | Uso do repertório |
| --- | --- | --- |
| Preparo | Planos abrem espaço para o gesto real; a frase ganha hierarquia sem esconder mãos ou xícara | Composição em camadas e tipografia; referência de profundidade sem copiar a órbita ou o neon |
| Convite | O espaço aberto vira área de leitura; a gravação continua enquanto 'pausa' ganha espaço e o CTA aparece | Continuidade e passagem de atenção entre estados; sem copiar a lista de passos das referências |

O percurso de estações do Finalizador continua disponível como alternativa de
repertório, mas não é obrigatório nesta direção: não há um processo factual de
três etapas a afirmar. Nenhuma biblioteca precisa aparecer só porque foi anexada.

O briefing anterior exigia desenho figurativo e três cenas. Não combiná-lo com
esta proposta. Para a futura montagem, usar o documento acima e este briefing:

> Construa o Reel fictício Café Pausa a partir da direção visual fornecida. Preserve
> integralmente gravação, ação, voz e kit confirmado. Desenvolva a ideia de abrir
> espaço para uma pausa com composição em camadas, tipografia e continuidade.
> Use somente fatos e materiais autorizados; sem preços, ofertas, destinos,
> ingredientes ou sincronismo inventados. O plano temporal e o código devem
> realizar essa direção. A aprovação dos quadros e do vídeo permanece pendente.

Na etapa 6, o montador deverá preencher `MotionRequest.scene_direction` com esse
JSON se a proposta continuar vigente, e selecionar `repertoire_id=business-reel-v1`.
Os IDs operacionais, fonte e orçamento não estão neste documento. Este arquivo
não despacha um pedido nem autoriza APIs ou produção. O pacote integral será
exportado pelo mesmo montador depois das etapas seguintes.

## Verificação

Passaram 228 testes direcionados de contexto, direção, plano, contrato, adaptador,
orquestrador e repertório. Cobrem captura/recaptura, modos e contagem do payload,
JSON da proposta, vínculo da resposta à direção e interrupção antes de efeitos
externos quando houver troca, IDs inválidos ou recurso indisponível. O novo
módulo `motion_visual_direction` atingiu 100% de linhas/ramos na cobertura dirigida.
Ruff, tipos dos seis módulos de produção e diff aprovados; sem CI global ou banco.
Nenhuma API real, geração de assets ou render executado.

Qualidade e fidelidade visual do HTML dependem dos quadros/vídeo posteriores;
igualdade do documento não prova execução. Etapa 3 concluída localmente;
o OK para a etapa 4 foi dado na solicitação seguinte. O estado vigente está no
[plano da refatoração](refatoracao-contexto-motion-2026-11-10.md).
