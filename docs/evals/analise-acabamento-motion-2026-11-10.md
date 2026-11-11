# Acabamento de motion: referências e auditoria da geração — 10/11/2026

## Escopo confirmado pelo titular

Postagens de negócio, inclusive gravações orientadas por roteiro nosso. Preservar
o vídeo do cliente é compatível com uma composição muito mais elaborada ao redor
dele. Edição de bruto para YouTube é outra ideia do titular, ainda não solicitada.
Não importar esse escopo nem tornar cortes do bruto requisito para o motion.
Kits, acervo, skills, biblioteca e infraestrutura existentes permanecem.

Feedback do Café Pausa B: mais elementos e melhora parcial, mas desenho infantil
e acabamento muito aquém do desejado. Não há aceite criativo final. Não concluir
que faltam referências fornecidas pelo titular: existem várias; a auditoria abaixo
mostra que não chegaram visualmente à última geração.

## Material efetivamente examinado

Downloads completos em 720p, com áudio, dos dois vídeos de Lucas Leite:

- [Aula prática, 37min53s](https://www.youtube.com/watch?v=zB0_5-e5V1Y).
- [Fluxo explicado, 8min46s](https://www.youtube.com/watch?v=W7E7Ln0z6aY).

[Relatório navegável local](../../.local/evals/raw-editing-references-20261110/report.html).
[Manifesto](../../.local/evals/raw-editing-references-20261110/manifest.json).
Amostras desde o início até o fim: 114 quadros a cada 20 s na aula e 66 a cada
8 s no vídeo curto. Detalhes a cada 2 s: abertura 0–40 s, aula 21:00–21:40 e
36:12–37:52. Sequência de 4 fps em 0:02–0:08 do vídeo curto. Café Pausa: três
quadros aprovados e sequência do MP4 a 2 fps. Isso não é escuta integral nem
verificação quadro a quadro dos 46 minutos; não foi certificada mixagem, fala
ou sincronismo exato. Os capítulos vêm da descrição do autor; alguns começam
antes da demonstração visual correspondente.

## Evidências visuais aplicáveis à postagem de negócio

| Trecho | O que aparece nas amostras | Técnica aproveitável sem copiar identidade |
| --- | --- | --- |
| Fluxo, 0:02–0:06 | Ícones contornam a pessoa em trajetória com diferenças de escala, foco e posição; palavra ganha destaque | Composição com profundidade e atenção coordenada sobre a gravação |
| Fluxo, 0:10–0:15 | Percurso curvo com elementos de edição muda de representação; aparece também tratamento desenhado | Ideia representada por relações/transformações; desenho não é, por si só, infantil |
| Fluxo, 0:26–0:30 | Card lateral de ferramenta, etiqueta e barra, com pessoa ainda visível | Objeto composto com hierarquia interna, sem preencher a tela com ícones avulsos |
| Aula, 36:45–36:49 | Comentários aparecem ao redor do apresentador | Elementos contextualizados e distribuídos em planos |
| Aula, 37:03–37:11 | Símbolo, pasta e interface mostram uma operação; gráfico muda de escala e o apresentador ocupa outra região | Ação visual com resultado, em vez de mera aparição de objeto |
| Aula, 37:33–37:51 | Grade de dias, indicador e painel de etapas desenvolvem informação ao lado da pessoa | Conteúdo progressivo dentro da cena, não somente troca de cartela |

Café Pausa B usa jarra/xícara em contorno simples, fundo amplo e plano, vídeo em
retângulo separado e hierarquia alterada em três momentos. A representação da
jarra vertendo líquido existe, mas a elaboração espacial e a riqueza de ações
permanecem inferiores às referências observadas. Essa diferença não é explicada
apenas pela quantidade de assets. O verde luminoso e as interfaces de tecnologia
não são prescrições para café, beleza ou outro negócio.

Medição auxiliar com a ferramenta de `claude-video`: abertura de 16 s tem amplitude
pico/mediana de aproximadamente 2,1×; Café Pausa, 8,5×. O índice maior no nosso
vídeo **não** demonstra acabamento melhor. As pausas ocupam cerca de 48% no nosso
e 12% no trecho de referência, segundo o limiar relativo da ferramenta. Filmagem,
épocas de transição, proporção de tela e área de fundo confundem essa medida;
não usar essas metas como nota de qualidade ou converter cortes detectados em
exigência de cortar o bruto. Os JSONs e limites ficam no relatório local.

## Por que as skills disponíveis não produziram o mesmo resultado

Auditoria do arquivo real `generation-request.json`, não só da configuração padrão:

| Fator | Evidência | Conclusão limitada |
| --- | --- | --- |
| Modelo | `gpt-6.1-sol`, esforço `high`, teto 64.000; resposta completa, 14.422 tokens de saída incluindo 5.696 de raciocínio | Esta geração não foi truncada. Não houve comparação controlada de modelos; não atribuir a causa ao modelo nem prometer equivalência |
| Referência visual | Seis imagens da fonte; `reference_context=[]`; calibrações de Intensa/Dog/Luma/Giz apenas textuais | O gerador não viu as referências de acabamento nesta rodada |
| Skill realmente enviada | `instagram-reel-v1`, 2.830 caracteres; três fichas locais de estilo | Não equivale a executar as skills completas de Maestro, Finalizador ou claude-video |
| Ferramentas | Sem ferramentas de navegação/arquivos na chamada; HTML/plano/direção produzidos juntos | O modelo não navega sozinho nas pastas locais ou nos exemplos. O serviço precisa selecionar e entregar o material relevante |
| Contradição | As três fichas incluem restrições do antigo executor: HTML não executável, áudio ainda não entregue, subset de cut/fade; instrução principal exige HTML/JS e executor atual mistura áudio | Incoerência comprovada no contexto. Efeito causal exato na qualidade ainda não medido |
| Direção da prova | Briefing exige preservar linguagem de desenhos figurativos, jarra/xícara/líquido/vapor, três cenas e janela sem recorte espacial | Escolha estreita preparada por nós; não demonstra o teto criativo do executor |
| Repertório incorporado | Componentes SVG e APIs de movimento existem; HTML/SVG/Canvas próprios permitidos. Exemplos completos das bibliotecas não são anexados à chamada | Há capacidades implementadas e repertório não transferido. Bibliotecas locais não se tornam capacidade aplicada automaticamente |
| Crítica | Última crítica truncou em 8.000 tokens; não houve parecer utilizável | O ciclo não validou/corrigiu este acabamento. Isso é distinto da geração completa |

[Resumo verificável da chamada, sem credenciais](../../.local/evals/raw-editing-references-20261110/generation-input-audit.json).
Locais de ajuste: `app/services/motion_context.py`, `motion_styles.py`,
`motion_skills.py`, `motion_creative.py` e `app/adapters/motion_ai.py`.
Não editar bytes de snapshots históricos para solucionar a incoerência: usar
nova versão ou projeção explicitamente versionada para o executor atual.

A skill Finalizador consultada seleciona cenas inteiras do catálogo e adapta
configuração ao trecho; não se limita a emprestar ícones. A pesquisa local
anterior já identificou 70 entradas. Nosso fluxo atual não executa esse seletor.
A skill claude-video prevê perícia da referência e comparação renderizada. No
produto, parte dessa mecânica existe, mas o alvo visual da última prova não foi
entregue ao modelo. Não é necessário mudar para um servidor Claude para transferir
essas práticas.

## Processo publicado pelo autor, separado da observação visual

O [repositório de Lucas Leite](https://github.com/LeiteZ/fluxo-de-edicao) distribui
um construtor de fluxo personalizado, não uma cópia pronta de todo seu fluxo.
Seu [guia de planejamento](https://raw.githubusercontent.com/LeiteZ/fluxo-de-edicao/main/guias/etapa-motion-mapa.md)
propõe conceito por ideia, camadas, atenção, batidas e saída; o catálogo serve de
repertório. Isso pode ser adaptado à gravação preservada, sem adotar a edição longa.
O [guia de construção](https://raw.githubusercontent.com/LeiteZ/fluxo-de-edicao/main/guias/etapa-motion-render.md)
trata feedback de qualidade geral como motivo para reconstruir a animação, não
só polir detalhes. O [guia de movimento](https://raw.githubusercontent.com/LeiteZ/fluxo-de-edicao/main/guias/oficio-motion.md)
separa velocidades de câmera/elementos, continuidade, hierarquia e legibilidade.
Esses números são referências de execução, não regras universais para cada marca.

## Próximo recorte recomendado — ainda não implementado nesta análise

1. Corrigir o pacote efetivamente enviado: eliminar contradições de executor,
   selecionar instruções úteis das skills e associar referência visual com
   tempo/proveniência/uso permitido. Verificar o payload antes de gastar.
2. Provar uma única cena de 6–10 s com a mesma gravação e kit, direção mais
   exigente e objeto/ação específicos. A gravação pode permanecer íntegra e
   visível; melhorar composição em camadas, tipografia, transições e ação visual.
   Mostrar quadro completo e sequência curta; desenho não deve ser obrigatório.
3. Se o resultado continuar abaixo do alvo, comparar modelos com exatamente
   o mesmo pacote de entrada, materiais e critérios, com orçamento separado.
   Um benchmark de uma cena informa mais que novas gerações completas sem controle.

Não instalar todas as skills, importar todas as bibliotecas ou aumentar chamadas
como solução automática. Não há evidência de que a plataforma Python/API seja o
limite; tampouco há prova de que o modelo atual atingirá o alvo com esses ajustes.
Nesta análise: zero chamadas pagas, zero mudança de runtime, zero testes/CI longos.
Documentação atualizada; próximos passos dependem do comando do titular.
