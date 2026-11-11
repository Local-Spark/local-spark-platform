# Próximas entregas para fechar o produto de geração

Data: 10/11/2026. Ordem proposta após o ensaio de alternância, cuja comparação MP4 local foi concluída na etapa de confiabilidade. Implementação
atual inclui os ajustes de motion e confiabilidade; esta lista não autoriza executar todas
as fases nem presume custos ou prontidão comercial. Base: plano da v0 de geração,
PROJECT, BL04 e contratos existentes. Documentos antigos que exigem postagem
na primeira entrega são históricos: o titular adiou essa integração.

## Sequência visual solicitada após a comparação

O titular priorizou tratamento da gravação, fundo participativo, objeto realista
e alinhamento com fala, autorizando uma etapa de cada vez. A etapa 1 foi
implementada em skill v8/movement-v3; a etapa 2 acrescenta fundo narrativo na v9,
com exemplo executável, direção e pacote offline. A etapa 3 acrescenta recorte
realista/sombra coordenada na v10, reutilizando o fluxo de imagens. Direção e
especificação de imagem preparadas; nenhuma imagem/peça nova foi gerada. As três
estão testadas, com qualificação visual pendente. Etapa 4 agora implementa ASR
local por palavra e vínculo fala→motion; falta provisionar/qualificar em execução
real. Comparação das quatro etapas aguarda OK e orçamento próprios.
Ver [fala alinhada](motion-fala-alinhada-2026-11-10.md).
Ver [objeto realista](motion-objeto-realista-2026-11-10.md).
Ver [tratamento](motion-tratamento-gravacao-2026-11-10.md) e
[fundo narrativo](motion-fundo-narrativo-2026-11-10.md). Essa sequência não substitui
a qualificação do fluxo e as features de fechamento listadas abaixo.

## Escopo de conclusão

Cliente pede → envia material quando necessário → acompanha geração → vê/ouve
prévia → pede ajuste → aprova versão exata → baixa arquivos. Kit, acervo,
bibliotecas, Python/API, PostgreSQL/RLS, ledger e Temporal permanecem.
YouTube longo, avatar/voz sintética, novos nichos e publicação automática não
bloqueiam a v0 de geração. Publicação Instagram não é acionada pelo aceite da peça.

## Atualização da etapa 1

Saída compacta com direção restaurada, metadados de respostas inválidas e limpeza
do subprocesso implementados. Comparação local concluída em 99 s após pausa
explicitamente autorizada de serviços em reinício contínuo; todos restaurados.
Ver [prova e limites](motion-confiabilidade-geracao-captura-2026-11-10.md).
O MP4 usa a resposta completa v6 preservada; não é geração nova com fundo/volume
v7. Qualificação paga do contrato compacto e correção dos serviços em reinício
continuam pendentes antes do piloto. O texto abaixo registra o diagnóstico que
motivou a etapa; não tratar as correções já feitas como trabalho ainda não iniciado.

## Gate imediato antes das próximas features

O ensaio revelou plano inválido, resposta truncada e captura lenta sob disputa
local de recursos. A etapa 1 implementou preservação de uso/custo em falhas,
saída compacta sem repetição da direção e limpeza de subprocesso; a comparação
local foi concluída sem aumentar limites, gerar assets ou chamar modelo.

Antes de liberar o piloto, provar uma geração completa pelo fluxo com o contrato
novo e resolver os serviços em reinício contínuo. Essa nova geração exige
orçamento próprio, não aproveita reservas anteriores e não deve virar repetição
cego de tentativas. Mantém-se uma chamada por efeito; falhas permanecem explícitas,
com evidência e orçamento. Recuperação automatizada de erro estrutural não foi
introduzida nesta fatia: uma futura ação exige identidade durável, limite e
admissão próprios, sem relaxar validação. Não atribuir truncamento ao modelo
sem investigar pedido, resposta e limites aplicados.

## Ordem de implementação recomendada

| Ordem | Entrega | O que aproveitar e o que falta | Critério de saída |
| --- | --- | --- | --- |
| 1 | Jornada completa do Reel e ajuste por linguagem natural | API motion-requests, content-pieces, decisões por hash e downloads privados já existem. Motion ainda tem qualificação restrita a negócio/material e não aceita entrada arbitrária em produção. Integrar pedido, seleção de fonte, progresso, erros, feedback e nova versão, sem transformar revisão em mera anotação. Tratar saída inválida antes do render com diagnóstico e recuperação explicitamente limitada por orçamento, sem reenvio cego ou relaxamento dos contratos. Auditar primeiro a UI disponível para não duplicar controles. | Pedir, visualizar, ajustar, aprovar e baixar pelo produto, sem script operacional; retry autorizado com identidade durável, aprovação invalidada pela nova versão, isolamento e custos corretos. |
| 2 | Fala alinhada e legendas opcionais | ASR local por palavra, confiança, tempos revisados e vínculo ao motion implementados. Qualificar com áudio real; completar UI de correção e legendas opcionais. Vídeos longos/cortes futuros. | Prova com fala autorizada, silêncio e ruído; motion/legendas no tempo observado, sem inventar falas e sem obrigar legenda em toda peça. |
| 3 | Story em vídeo | Reutilizar Reel, contrato de peça e executor. MotionRequest atualmente aceita somente reel. Criar contexto/skill/enquadramento e habilitação próprios do formato. | Arquivo vertical, leitura, áreas úteis, áudio e ciclo de revisão/download validados; não apenas novo rótulo de formato. |
| 4 | Carrossel com motion | Contrato de peça já representa coleção ordenada e pedido de mudança por página. Falta gerar/renderizar e recuperar coleção de 3–5 MP4s de 5–8 s, em 4:5, com fluxo completo. | Ajuste preserva páginas não afetadas; expansão depende da confirmação do cliente; versão da coleção exige novo aceite; download ordenado e falha parcial recuperável. |
| 5 | Fechamento da qualidade por formato | Retomar gate BL04.3 de feed/story e avaliar Reel/story em vídeo/carrossel. Medir custo completo, tempo, rejeição e correções, incluindo falhas. Não usar uma cafeteria como prova universal. | Casos acordados em celular, fatos/kit corretos e arquivos aceitos; preços/franquias fundamentados em custo por peça aceita. |
| 6 | Piloto operacional | F07/F08: franquias, orçamento, cobrança existente, staging, storage privado, métricas/alertas, suporte, backup/restore e recuperação. BL05 conecta a jornada a WhatsApp simulado e depois oficial; homologação não impede desenvolvimento local. | Cliente da coorte consegue completar o ciclo e recuperar falhas, com acesso, consumo e suporte verificáveis. CI completo e integração antes de merge/liberação; testes curtos por fatia durante desenvolvimento. |

Após o gate de confiabilidade, a próxima feature é a **jornada do Reel com ajuste e nova versão**.
Não reabrir indefinidamente a linguagem criativa para liberar cada botão. Se o
objetivo imediato for comprovar motion ligado à fala, executar a entrega 2 antes
de ampliar formatos. Não habilitar produção removendo apenas a guarda de qualificação.

## Objetos com aparência mais realista: viabilidade

O pedido adicional é viável como evolução visual, mas a aparência 3D e a geometria
3D são capacidades distintas. O código atual oferece PNG transparente com
proveniência, reserva, persistência e reuso (`motion_illustration_policy.py`,
`motion_illustrations.py`), além de assets autorizados, SVG/Canvas e animação.
Não há modelo de malha, iluminação 3D ou pipeline de objetos giratórios validado.

Primeira opção recomendada: uma xícara conceitual com acabamento de cerâmica,
volume e luz, recortada, tratada como objeto em camadas. Movimento contido de
posição/escala/rotação no plano, sombra de contato separada, vapor e superfície
do café coordenados podem dar presença e profundidade. A direção deve planejar
quais partes ficam na frente/atrás; um PNG inteiro não fornece automaticamente
máscara interna, geometria, mudança de luz nem visões de outros lados. Preenchimento
não deve tornar cerâmica opaca artificialmente transparente para mostrar o líquido.

Isso é 2.5D: uma imagem sozinha não sustenta rotação volumétrica de 360 graus ou
revelação consistente da parte traseira. Para esse requisito, estudar asset 3D
licenciado e extensão do executor com dependências fixadas, render determinístico,
isolamento, suporte e custo próprios. Não instalar um novo motor sem prova de
necessidade e sem avaliar o ganho de uma única cena.

O pipeline de ilustrações já limita a geração a objetos conceituais, não fotos
documentais do produto/pessoa/local do negócio. Se a peça precisa mostrar a xícara
ou produto real vendido, a fonte deve ser material autorizado do cliente. Uma
ilustração pode ter material convincente sem ser apresentada como evidência real.

Prova futura delimitada: uma única cena com objeto/asset apropriado, mesma paleta
e mensagem, comparada ao desenho atual. Primeiro decidir representação/camadas,
depois medir o asset efetivamente produzido e sua integração. Não prometer que a
qualidade do asset ou uma rotação CSS, isoladamente, entregam acabamento de estúdio.
É opcional para fechar a jornada inicial, e não uma exigência para todo negócio.
A rodada de alternância autorizada exclui imagens pagas; nenhuma foi gerada para
esta análise. Autorização e orçamento próprios antes de qualquer prova com geração.

## Fundo e vídeo também precisam de direção

Feedback posterior: a última peça tinha fundo quase invariável e gravação em
janela de tamanho fixo que mudava de lugar para acomodar a xícara. Orientações v7
passam a pedir, quando a direção requer elaboração, função para os planos de fundo
e para enquadramento/moldura/escala/revelação da gravação. Não basta melhorar o
asset da xícara e manter o restante passivo. Realismo de um asset não substitui
coreografia do quadro inteiro. Preservar o kit não significa preservar fundo liso.

Essa orientação foi implementada após o despacho da rodada de alternância v6;
a comparação local concluída não comprova a v7. Uma prova visual futura deve avaliar
cena completa, com objeto, fundo e gravação coordenados, sem multiplicar rodadas
para cada efeito isoladamente. Esta pendência deve ser comunicada antes de alegar
que o alvo criativo completo foi atingido; não exige novos serviços ou tabelas.


## Pendências de confiabilidade comprovadas nesta rodada

A geração inicial retornou JSON completo com dois beats sobrepostos no mesmo
elemento e foi bloqueada antes do render. Além dos dois defeitos corrigidos,
a jornada precisa oferecer diagnóstico/recuperação de saída inválida antes de
criar uma peça, com efeito durável próprio e limite de tentativas/custo. Isso não
é licença para repetir resultados incertos ou aprovar uma composição inválida.

O adaptador preserva a resposta bruta, mas perde os campos estruturados de uso e
estimativa ao rejeitar uma resposta completa inválida. Nesta rodada foi possível
reconciliar localmente US$ 0,308018 pelo uso retornado; o ledger permaneceu sem
estimativa e o hold foi mantido. Corrigir essa propagação de metadados em uma fatia
curta antes do piloto, sem alterar retroativamente a evidência ou tratar ausência
de estimativa como custo zero. Esse diagnóstico não foi corrigido silenciosamente
na imagem do worker já despachada.


Medição da primeira saída completa desta rodada, em JSON canônico: 39.029 bytes,
dos quais 9.040 (23,16%) repetem scene_direction já fornecida. O plano ocupa
17.975 bytes. É evidência de redundância removível na serialização; não é contagem
de tokens nem prova de que eliminar o eco resolve a interrupção. Artefato local:
`reel-alternancia-20261110/output-size-analysis.json`.


A captura local também falhou: limite integral de 600 s e timeout do navegador
na tentativa em trechos, com cancelamento pendente do script diagnóstico. Incluir
reprodução curta de seek/captura e encerramento de subprocesso no gate imediato.
Não alegar peça entregue com base nos três quadros parciais nem ampliar limites
sem diagnóstico. Nenhum serviço ou runner adicional foi introduzido.
