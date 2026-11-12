# Revisão da peça atual — acabamento, som e evolução contínua

## Atualização — interpretação do feedback e estudo em trechos, 12/11/2026

O titular aponta um problema recorrente: exemplos de acabamento são tratados
como regras e passam a dominar a próxima direção, deslocando qualidades já
aceitáveis. Sugere estudar/trabalhar aproximadamente 4–5 segundos por vez para
aprofundar a riqueza gráfica, sonora e o impacto. Isso orienta um experimento;
não define duração máxima do produto, montagem em blocos independentes ou
intensidade obrigatória em cada instante. A análise de 11/11 abaixo é mantida.

**Mecanismo confirmado nos arquivos.** A skill v13 já declara borda opcional e
permite variar a visibilidade da gravação. Entretanto, a direção de recuperação
fixa abertura, moldura, representação da xícara e funções dos elementos; o brief
limita a intervenção às passagens. `provided_direction_contract` exige construir
a direção fornecida e `validate_direction_fidelity` protege sua identidade.
Essas proteções não distinguem uma decisão artística boa de uma hipótese fraca.
O diagnóstico da regressão anterior já documenta a reescrita ampla que retirou
funções de ligação. Não há evidência de uma regra global atual exigindo borda,
xícara fotográfica ou vídeo visível o tempo todo. O problema inclui a interpretação
e a direção preparadas pelo assistente antes da execução, não apenas a skill.

**Como interpretar o feedback nas próximas direções.** Registrar, junto da
decisão, sua origem e alcance: requisito explícito vigente, observação sobre um
artefato, exemplo de possibilidade ou hipótese do assistente. “Faltou borda” não
determina borda em todas as cenas; “xícara real” não elimina outras representações
de todo o repertório; preservar a gravação/voz não impõe presença visual contínua.
Preservar o patamar significa comparar as qualidades e funções, sem congelar
todos os elementos e layouts. Escolhas limitadas à rodada anterior não viram
normas permanentes. Uma ambiguidade que impeça decidir será levada à entrevista;
não é necessário solicitar confirmação de cada decisão artística rotineira.

**Unidade de trabalho proposta.** Estudar uma ação completa de cerca de 4–5 s
da referência, com contexto imediatamente anterior/posterior. A sequência próxima
de 02:40 é candidata para luz/camadas; os limites exatos dependem da ação completa.
Mapear fala, foco, planos, luz/material, enquadramento, preparação, acento,
repouso, passagem e som. Distinguir observado de inferido; amostras estáticas não
comprovam curvas, fluidez ou áudio. Ainda falta esse estudo temporal e a escuta.

Aplicar o mecanismo pertinente a uma janela da peça atual, mantendo o roteiro
completo e o relógio absoluto. O intervalo 4,220–8,440 s continua uma hipótese,
não um recorte obrigatório. Definir imagem e intenção sonora em conjunto;
comparações isoladas de som ajudam a diagnosticar a contribuição, mas não impõem
uma ordem criativa universal. Cada janela deve ter contexto de entrada/saída,
hierarquia e continuidade com a peça inteira. Não cortar a fala ou gerar clipes
independentes para contornar o contrato atual. Não há novo modo de geração por
trecho implementado: eventual suporte deve usar o montador/executor existentes.

Antes de fixar a nova direção, explicar quais funções permanecem, quais mudam e
por que a mudança pode melhorar a experiência. Só substituir a referência após
comparar o resultado em movimento e som, dentro do conjunto. Riqueza não será
medida por quantidade de efeitos ou ocupação de todos os instantes: preparação,
ênfase e repouso precisam servir à fala. Capacidade técnica continua distinta de
qualidade comprovada; nenhuma promessa de melhora automática em cada tentativa.

Escopo desta atualização: conferência de código/brief/direção e documentação.
Nenhum código de produção, artefato anterior ou staging alterado; nenhuma geração,
chamada paga, renderização, acesso a banco ou inicialização de serviços. Validação
documental por diff; sem testes de runtime ou novo aceite audiovisual. Pendem o
estudo curto em movimento/escuta, sua aplicação verificável pelo fluxo real e as
pendências de persistência/seleção já registradas abaixo.

## Auditoria de 11/11/2026

Data: 11/11/2026. Escopo desta entrega: análise da peça, dos recibos reais e das
referências já disponíveis; prioridades para implementação. Nenhum código de
produção, orçamento, banco ou serviço alterado; nenhuma chamada paga, imagem ou
composição nova renderizada. Não é reinício das etapas 1–7.

## Feedback e patamar a preservar

O titular gostou da nova peça, considerou-a melhor que a última gerada e percebeu
retomada da evolução. Ainda a considera distante da referência Maestros: pede
mais impacto, presença do ambiente e desenho sonoro, citando fundo/degradê,
elementos e som de líquido como exemplos, não receitas obrigatórias.

Arquivo: `.local/evals/motion-recovery-run-20261111/nova-peca-avaliacao.mp4`.
SHA-256: `e4bfabe68500189d6cd147f440f8ef4f2bccabd6e3001dff08cebf9e7e5d47f0`.
Este feedback estabelece uma referência de continuidade para a próxima avaliação.
Não equivale a aceite final de todas as dimensões nem à aprovação de uma versão
persistida que não existe: o pedido do produto continua falho. As duas bases
anteriores continuam no histórico; não substituí-las silenciosamente.

Preservar gravação/voz, kit, identidade da xícara, continuidade entre gravação e
motion, participação do objeto no encerramento e capacidade de explicar a fala.
Preservar essas funções não exige congelar os mesmos retângulos, enquadramentos,
curvas ou horários de preparação. Substituições devem ser declaradas na direção
antes de construir, mantendo evidência de não regressão.

## Evidência desta revisão

Conferidos plano, composição e entrada efetiva de implementação da rodada R5;
inspecionados quadros decodificados do MP4 e as sequências locais da referência
em 02:40–02:48 e 04:34–04:42. Releitura dos relatórios de referência, do contrato
e da etapa 5, confrontados com código atual. Não houve escuta nesta revisão nem
visualização contínua integral da referência; não atribuir notas de fluidez/áudio
a essa inspeção. Auditoria local: `.local/evals/motion-cinematic-audit-20261111/audit.json`.

| Observação concreta | Implicação e limite |
| --- | --- |
| Há 18 elementos declarados; retorno mostra gravação e xícara | A falta percebida não se explica pela contagem de objetos. Investigar hierarquia, relações e tempo útil. |
| Vídeo da abertura assenta até 0,620 s; aproximação posterior de 2,5% | Existe movimento, mas a direção restringe seu contraste e a mudança de enquadramento. Não prova que acelerar tudo melhoraria. |
| Gravação fica coberta até 4,220 s; xícara começa a entrar em 6,780 s | 2,560 s são sustentados principalmente por texto/percurso/apoio. É uma oportunidade concreta de preparação mais expressiva, não ordem para cortar a fala. |
| Em 5,600 s predominam painel claro, texto e região vazia | A preparação declarada não forma um ambiente visualmente forte. O vazio pode ser pausa intencional, mas aqui o titular sente falta de elaboração. |
| `cafe-apoio` já usa `linear-gradient` com alfa inicial 0,065 | Não falta apenas uma função CSS. O degradê existe, mas é sutil e restrito ao apoio; não demonstra luz/profundidade da cena. |
| Xícara é PNG conceitual, com entrada diagonal, escala, sombra e vapor separados | Há presença recuperada, mas não geometria volumétrica. Luz, apoio, escala e ambiente precisam concordar. Não prometer revelar o verso da imagem. |
| `sound_events=[]`, sem `authorized_soundtrack`; uma faixa `assets/source.mp4`, ganho 1 | Não houve camada sonora adicional. Isso não prova ausência de ruído de líquido dentro da gravação; falta escuta. |
| Payload contém Maestros em 80/84/88 s e duas imagens de Lucas | A referência está sendo usada; a seleção Maestros enfatiza trajetória. Os trechos de luz/câmera/ambiente de 160–168 s e 274–282 s não foram as imagens selecionadas desta rodada. |
| Houve duas chamadas pagas: plano e implementação | A crítica paga de movimento/som não aconteceu. A prévia passou por verificação técnica e foi vista pelo titular; não houve ciclo criativo completo de revisão/correção. |

Na referência, as sequências inspecionadas mostram superfícies iluminadas,
sombras relacionadas à luz, camadas com oclusão e mudanças de enquadramento que
revelam relações. São mecanismos observáveis a adaptar ao kit. Não copiar tema,
paleta, pessoas, textos ou mídia da referência para o cliente. O vídeo apresenta
um processo com iteração e várias ferramentas; a demonstração não disponibiliza
os bastidores completos nem garante equivalência com uma chamada do produto.

## O que “cinematográfico” deve significar neste caso

Trabalhar propriedades perceptíveis, com comparação, em lugar de um adjetivo no
prompt:

- **Luz e material:** objeto, sombra e superfície parecem pertencer ao mesmo
  ambiente; o fundo ajuda a perceber volume e separação de planos.
- **Enquadramento:** uma aproximação/revelação muda o que o espectador entende,
  preservando mãos, jarra e xícara na gravação. Movimento de câmera serve ao foco.
- **Ritmo:** existe contraste entre preparação, acento principal e repouso;
  a leitura e a pausa continuam confortáveis.
- **Som:** um acontecimento selecionado ganha presença audível sem competir com
  a voz, duplicar o som original ou sugerir uma ação que não está acontecendo.
- **Informação visual:** luz, contato, escala e transformação contam algo sobre
  a experiência. Isso não autoriza inventar atributos comerciais nem preencher
  o quadro com ícones sem função.

O kit admite exploração; fundo claro não é um defeito universal. Um campo escuro
ou degradê também pode ficar chapado. Uma câmera simulada em camadas pode ser
suficiente; Three.js, outra plataforma ou asset 3D só entram se uma cena concreta
exigir uma capacidade que o executor atual não consiga entregar.

## Lacunas reais do fluxo

**Som: capacidade de mixar não é direção sonora entregue.** A etapa 5 implementou
seleção explícita pela API, material autorizado, fades, ducking da música,
proteção do ramo original e medições. `MotionSoundEvent` diz expressamente que
o evento é selecionado pelo titular, nunca inferido de prompt. Não há hoje um
caminho completo que escute a ação, proponha efeito adequado, apresente opções,
confirme origem/direitos, posicione e valide uma comparação sonora. Nesta rodada,
a opção anterior de somente gravação original foi respeitada. O feedback atual
pede explorar som nas próximas comparações; não foi autorizada a compra/geração
de um asset específico nem selecionado um arquivo. Não inventariamos o acervo
sonoro nesta revisão e não afirmamos que ele esteja vazio.

**Referência selecionada não corresponde a todas as qualidades desejadas.** Para
avaliar ambiente e câmera, selecionar uma pequena sequência que os demonstre,
com mecanismo, instante e função esperada na candidata. Manter o orçamento de
contexto, trocando referências de menor pertinência quando necessário. Verificar
essa seleção no payload real. A aprovação não deve ser “há cinco imagens”, mas
“a relação espacial observável desta sequência foi aplicada com resultado”.

**A direção protege também escolhas fracas quando prescreve demais.** O brief de
recuperação preservou a abertura e delimitou a mudança às passagens. Foi útil para
recuperar o patamar; limita a ambição de um redesenho sensorial. O plano fixa
painel papel, posições e amplitudes pequenas. Evoluir essas escolhas requer rever
a direção explicitamente, não quebrar fidelidade no código gerado nem remover
as proteções existentes.

**Conclusão do contrato e avanço localizado estão misturados na seleção.**
`evolution_verdict` exige quatro dimensões criativas melhores; `choose_candidate`
rejeita `partial`. Isso impede reconhecer, por exemplo, espaço melhor com os
outros aspectos preservados. O contrato exige as quatro melhorias para concluir
a evolução global; não significa que cada experimento precise melhorar tudo de
uma vez. Propor distinção explícita entre incremento comprovado, recuperação do
patamar e conclusão do contrato. Nenhuma regressão bloqueante ou evidência
insuficiente passa a ser aceita. Som precisa de evidência própria: a rubrica
`baseline_checks` atual não inclui uma dimensão sonora e uma crítica de imagens
não pode aprová-la. Essa mudança é proposta, não implementada nesta análise.

**A nova peça apreciada ainda não é selecionável como base persistida.** O
vínculo atual exige versão em `motion_render_versions`; a prévia foi entregue por
operação separada enquanto o pedido permaneceu falho. Preservar o arquivo/hash
e o feedback agora e corrigir a integração de aprovação/artefato antes de promover
uma referência no banco. Não fabricar recibos, sobrescrever o passado nem declarar
recuperada a igualdade dos quadros que divergiu.

## Próximas intervenções, dentro do contrato existente

| Prioridade | Intervenção delimitada | Evidência para decidir se vale manter |
| --- | --- | --- |
| Base e confiabilidade | Preservar esta versão e resolver captura/persistência com testes que percorram o fluxo real; distinguir incremento do fechamento global | Artefato selecionável com origem/decisão corretas; nenhum provider repetido indevidamente; testes de falha e não regressão |
| Primeiro experimento visual | Desenvolver o trecho de preparação/revelação da xícara, aproximadamente 4,220–8,440 s, usando a mesma imagem e o kit; referências de luz/camadas pertinentes | A/B com a atual, sem mudar o som: preparação mais perceptível, objeto apoiado, mudança de foco clara, leitura e retorno preservados |
| Experimento sonoro separado | Escolher poucos eventos motivados e materiais autorizados; manter o vídeo exatamente igual no A/B | Escuta com/sem complementos; ação e som coerentes; voz inteligível, sem duplicação, picos controlados; sem aprovar som pelos PNGs |
| Depois, abertura | Avaliar detalhe/reenquadramento e presença inicial da ação real | Comparação própria que proteja mãos/jarra/xícara e mostre ganho de atenção sem desfazer a continuidade aprovada |

Hipótese visual inicial para Café Pausa: fazer o fundo deixar de funcionar como
um cartão e passar a sugerir uma superfície iluminada; variar contraste dentro
da paleta, coordenar aproximação das camadas e revelar a xícara sobre esse apoio.
A preparação pode mostrar um detalhe/indício antes do acento em “Café”; o acento
não precisa ser o primeiro instante de qualquer informação sobre o objeto.
Isso exige um plano revisado e conferido com o timing existente, sem mudar a voz.
Manter o objeto no retorno e o convite legível. É uma hipótese para cards e
comparação, não uma garantia de acabamento nem uma regra para outros negócios.

No som, o exemplo de líquido é pertinente durante o gesto visível da gravação,
se a escuta confirmar necessidade. Não colocá-lo automaticamente na aparição de
uma xícara estática. Um contato no apoio pode ser outra hipótese, condicionado
à ação e ao material. Música não é obrigatória e não substitui desenho sonoro.

## Revisão recorrente por rodada

Antes da geração, registrar uma hipótese perceptiva, o trecho afetado, a evidência
da referência, o material necessário e o que deve permanecer. Usar o montador do
produto e conferir o payload, não uma demonstração manual separada.

Depois de cada artefato, realizar a comparação antes de anunciar melhoria:

1. Inspecionar começo, preparação, acento, passagem e encerramento nos instantes
   relevantes; verificar a sequência em movimento, não apenas quadros bonitos.
2. Separar o declarado, o implementado e o percebido. “Sombra presente” não prova
   contato convincente; “evento sonoro configurado” não prova mixagem boa.
3. Registrar os até três problemas de maior impacto, com instante, evidência,
   consequência e menor correção plausível. Não trocar toda a peça a cada revisão.
4. Comparar a dimensão-alvo e as protegidas. Empate não é melhoria; regressão
   bloqueante impede promoção; evidência ausente permanece “não avaliado”.
5. Ouvir o resultado quando houver decisão sonora, conferir métricas técnicas e
   manter o parecer do titular. Incorporar o que funcionou sem perder a base.

Para cada problema, preencher: **instante → observação → causa provável/confiança
→ intervenção → resultado esperado → como comparar → resultado observado**.
Para isolar a contribuição de um efeito sonoro, comparar o mesmo vídeo com/sem
esse efeito. Isso não impede conceber imagem e som em conjunto nem exige separar
toda decisão criativa em rodadas distintas. Sem novos serviços/tabelas/runner
para iniciar esse trabalho. Custos de produção futuros continuam sujeitos à
proposta e autorização específicas; o teto antigo não autoriza novas rodadas.

“Constantemente”, neste escopo, significa executar esse ciclo a cada rodada e
incorporar o feedback ao contexto do próximo trabalho; não monitoramento em
segundo plano ou tarefa agendada. Esta entrega registrou o protocolo e auditou
o caso. A automação do ciclo ainda requer implementação e validação.
