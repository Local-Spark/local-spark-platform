# Executar o ensaio de motion em um comando

Este documento descreve o executor existente de **uma composição**. O novo
CLI privado `scripts/evals/motion_review_eval.py` e seus comandos de crítica e
correção constam no [plano do ciclo](plano-ciclo-revisao-motion-2026-11-06.md).
Comandos históricos desta página não ampliam o orçamento de outras rodadas.

O modo rápido foi escolhido pelo titular em 06/11/2026: gerar o MP4 e avaliar
somente o resultado final. Nesse modo, as aprovações intermediárias de cards e
frames da skill `claude-video` foram dispensadas expressamente. O comando é um
executor local de avaliação criativa; não exige banco, Temporal, WhatsApp ou Meta.

## Uso

Para a rodada preparada de três linguagens, conferir sem gasto:

```sh
make motion-diversity-eval
```

Após autorização específica do orçamento/envio desta rodada:

```sh
make motion-diversity-eval EXECUTE=1 BUDGET_USD=2.25
```

O relatório de lote compara três peças com v2/intensa; a concorrência é dois,
com render serializado. Não executar esses mesmos pedidos pelo CLI individual:
a proteção entre comandos ainda não é bidirecional.
[Plano, fontes, orçamento e limites](plano-motion-diversidade-2026-11-06.md).

Na raiz de `local-spark-platform`, conferir o cenário e o plano sem gastar:

```sh
make motion-eval
```

Para executar a geração e abrir a comparação:

```sh
make motion-eval EXECUTE=1 BUDGET_USD=0.75
```

O segundo comando autoriza um envio pago desse cenário para
`https://api.openai.com/v1/responses`, limitado à reserva informada antes de
iniciar a chamada. Ele transmite os quadros, contexto, referências, código e
instruções identificados no cenário. O cenário inicial contém somente material
fictício do ensaio, fontes abertas e composições locais; não usar conteúdo real
de cliente neste recorte. O teto controla iniciar uma chamada, não a cobrança do
fornecedor depois do envio. Credencial configurada:
`MEU_BRACO_DIREITO_OPENAI_API_KEY`, no ambiente ou `.env`; não colocá-la no comando.

O cenário padrão é
`.local/evals/motion-library-round-2026-11-06/proposal/cafe-reel-library.json`.
Ele inclui a skill própria de Reel e código selecionado da biblioteca, com v2
como piso e comparação da rodada anterior. [Plano e orçamento](plano-motion-biblioteca-2026-11-06.md).
Para outro cenário preparado, usar `MOTION_CASE=<caminho-json>` no mesmo comando.
Cada cenário fixa o pedido enviado, hashes, mídia, kit, referências, áudio,
perfil e ferramentas. Esta primeira fatia não transforma uma gravação arbitrária
em cenário automaticamente. Arquivos privados em `.local` não vêm em outro
checkout. As dependências devem existir localmente; o comando não as instala.

## O que esta execução faz

1. Confere cenário, hashes, arquivos e ferramentas antes de gastar; apresenta
   modelo, reserva e orçamento. A primeira configuração usa `gpt-6.1-sol`,
   esforço alto e até 32.000 tokens de saída. A estimativa é US$ 0,25–0,60 e a
   reserva é US$ 0,75 para uma chamada, sem refação automática.
2. Reaproveita a interpretação Jev, a transcrição e a direção histórica
   identificadas no caso. Não registra chamadas novas para essas etapas.
   O modelo recebe quadros e texto; não ouve nem assiste ao clipe completo.
3. Pede a composição executável completa: HTML/CSS, JavaScript com relógio
   explícito e plano de áudio. Recebe código real das referências, incluindo
   os motores selecionados da biblioteca; preserva a resposta original.
4. Vincula somente os arquivos autorizados, executa a cena no Chromium com
   sua sandbox normal e recursos locais controlados, e monta vídeo/áudio com
   FFmpeg. O JavaScript de cena roda na página, nunca como código Node.
5. Salva resultado e relatório numa pasta UUID em `.local/evals/motion-runs/`,
   com comparação, MP4, request/response, hashes, trace e custo estimado. O
   resultado não é declarado criativamente aprovado por ter sido renderizado.

Cada execução tem identidade própria e reserva durável antes da rede. Falhas
ou resultado incerto preservam o registro; o comando não tenta novamente por
conta própria. Não reexecutar scripts históricos para tentar recuperar uma
chamada. O relatório permite localizar a resposta recebida e reaproveitá-la
offline, sem outro pagamento.

## Recuperação explícita de saldo insuficiente

Após corrigir o saldo e autorizar **uma nova operação com novo orçamento**, o
CLI permite recuperar somente uma rejeição HTTP 429 registrada com
`insufficient_quota` / `credit_balance_exhausted`, sem saída e com uso ausente
ou objeto vazio. Uso vazio sozinho não prova que uma chamada deixou de ocorrer.

```sh
make motion-eval EXECUTE=1 BUDGET_USD=0.75 RETRY_REJECTED=1
```

Não apagar marcadores nem ledgers. O comando cria UUID, reserva e marcador
sucessor exclusivos, vinculados aos hashes da rejeição anterior. Preserva todas
as reservas e custos anteriores, inclusive valores desconhecidos; não presume
reembolso ou cobrança zero. Rate limit, timeout, resposta incompleta, uso
informado, saída presente ou evidência alterada continuam bloqueando reenvio.
Sem a opção explícita não há recuperação automática; depois de sucesso, a mesma
entrada reaproveita o resultado sem nova cobrança.

Validação da extensão: 25 testes offline passaram, incluindo recuperação da
rejeição conhecida, bloqueio de estados incertos e preservação dos registros;
Ruff e mypy strict aprovados. Nenhuma API foi chamada pelos testes.

## Conferência offline

O cenário inclui uma resposta local conhecida que reproduz somente o Reel v2
aprovado. Ela serve para verificar o comando e o renderer sem nova geração:

```sh
make motion-eval MOTION_CASE=.local/evals/motion-quality-reset-2026-11-06/one-command/cafe-reel.json RESPONSE=.local/evals/motion-quality-reset-2026-11-06/one-command/replay-v2.json
```

Essa execução deve aparecer como replay offline, custo novo zero e referência
histórica. Ela não prova que uma futura direção do modelo ficará melhor.

## Validação desta fatia — 06/11/2026

- Preflight do alvo Make, 15 testes offline de orçamento/reenvio/transporte,
  validação de resposta/arquivos/áudio e três testes Node do mixer passaram;
  Ruff e mypy strict do CLI passaram. Os testes offline foram ligados a
  `motion-eval-test`, que é pré-requisito de `motion-test` no CI.
- Uma execução completa de `motion_eval.py --from-response` gerou relatório,
  sete quadros e MP4, preservando cópias próprias dos assets, referência e três
  avisos de direitos. [Relatório da prova](../../.local/evals/motion-runs/1288526d-8ab1-455f-a70a-35b542541068/report.html).
- A saída teve SHA-256
  `2e9e38be97240745a7f5abbfa3dfea3962d445375f2df48575c6968bef4cb7d0`,
  igual à referência WAAPI. Modo offline, reserva/custo novos zero, nenhuma API.
  A reprodução direta pelo renderer também verificou sete amostras e o áudio.
- A última alteração somente do relatório disponibiliza HTML/JS também como
  texto para inspeção; não exigiu repetir a codificação do vídeo. A prova
  histórica permanece intacta. CI integral da aplicação não foi repetido
  nesta fatia; validação do provedor e qualidade de uma nova composição
  permanecem para a execução paga explícita.

## Limites deste recorte

### Ferramentas locais na retomada de 08/11

Os binários macOS verificados foram preservados em
`.local/tools/motion-lab/bin/ffmpeg` e `ffprobe`; os arquivos de distribuição e
`manifest.json` no diretório pai registram versões, origem e hashes. Ver o
[inventário e recuperação](../design/motion-dependencias-linux-2026-11-05.md#recuperação-do-laboratório-macos--08112026).
Os testes localizam essas ferramentas por variável explícita, PATH ou esse
diretório persistente. Em Linux, instalar o pacote FFmpeg que também fornece
FFprobe; o CI faz essa preparação antes dos testes.

Os casos históricos congelados ainda apontam para os caminhos temporários
originais. Na recuperação foram criados links desses caminhos aos binários
persistentes, depois de conferir os hashes; não modificar os manifests, apagar
operações incertas ou usar `--execute` como verificação de ferramentas. Se os
links desaparecerem, recuperá-los somente para os bytes verificados registrados
no manifesto. Fazer o preflight local antes de qualquer efeito pago.

Sandbox do navegador, CSP e interceptação controlam os recursos da página;
não constituem confinamento de rede/arquivos de todo o sistema operacional ou
ambiente de produção. A ferramenta limita-se a fixtures fictícias, sem
credenciais no processo do navegador, e interrompe se faltar recurso ou houver
falha técnica. Não contorna restrições usando `--no-sandbox`. A geração por
modelo não é determinística; o cenário e a composição recebida ficam congelados
para comparação. Os binários locais temporários ainda precisam ser empacotados
antes de uma entrega de produção.

O comando não muda a jornada do produto nem substitui Temporal no runtime.
A geração por modelo só será validada ao executar a chamada; as provas locais
de replay e HTTP simulado verificam a orquestração. Registrar separadamente
qualidade humana, uso estimado e fatura. Preservar as licenças/atribuições que
acompanham código, gravação e áudio ao compartilhar os resultados.
