# Diagnóstico das três interrupções de motion

Análise solicitada pelo titular em 11/11/2026. Leitura dos payloads e corpos de
resposta preservados, inspeção do código e consulta à documentação oficial.
Nenhuma geração, imagem, render ou chamada paga. Nenhuma mudança de produção.

## Conclusão e limites

Causa imediata comprovada: a API retornou status incomplete com motivo
max_output_tokens e a string scene_init sem fechamento nas três tentativas.
O corpo HTTP externo foi recebido e é JSON válido; o JSON da composição dentro
dele é que está incompleto. O produto preservou o retorno/custo e interrompeu o
fluxo antes de imagem/render/crítica. Não foi o Docker cortando um vídeo.

A causa raiz do limite reportado pelo provedor não está comprovada. Em todos os
casos, usage.output_tokens foi inferior ao max_output_tokens solicitado e
retornado. Não é correto apresentar essa discrepância como prova de que o modelo
esgotou 54/64 mil tokens, tem janela de 64 mil ou é incapaz de criar a peça.

## Comparação dos retornos

| Tentativa | Entrada | Teto de saída | Saída reportada | Raciocínio, incluído na saída | Plano completo, bytes | Beats |
|---|---:|---:|---:|---:|---:|---:|
| Inicial | 34.928 | 64.000 | 25.722 | 15.020 (58,39%) | 21.984 | 52 |
| Instrução enxuta | 35.075 | 64.000 | 19.856 | 8.804 (44,34%) | 23.850 | 63 |
| Contrato compacto v2 | 35.340 | 54.000 | 27.924 | 18.425 (65,98%) | 17.902 | 37 |

Bytes são JSON minificado UTF-8 do campo motion_plan completo; não equivalem a
tokens. Na terceira, output_tokens menos reasoning_tokens = 9.499; isso não é
contagem exata de texto visível, pois pode incluir tokens internos de formatação.
Nenhum raciocínio oculto foi lido para esta análise; somente contagens agregadas.

O ganho offline de 20,87% era real para a representação do MESMO plano de 63 beats.
A terceira geração criou outro plano (37 beats) e consumiu mais raciocínio. Logo,
a igualdade do conversor e a redução de bytes não provavam redução do custo de
raciocínio ou conclusão da próxima resposta. Essa inferência não deve ser feita.

## Achados confirmados no produto

1. Os 12 inputs estavam presentes nos três pedidos, com detail=high: seis quadros
   da gravação e seis referências. O hash da fonte permaneceu igual. Esta falha
   não é a ausência de referências identificada na auditoria antiga.
2. O pedido reúne plano temporal, descrições, HTML, JavaScript e especificação de
   imagem em uma resposta indivisível. Qualquer string truncada impede obter a
   composição validada. As partes completas são preservadas como resposta bruta,
   mas não há retomada por artefato validado no fluxo atual.
3. request_bytes usa sort_keys=True recursivamente. Isso altera também a ordem
   de properties do JSON Schema. Ordem efetivamente enviada/observada:
   audio → concept → html → illustrations → motion_plan → scene_init → source_usage.
   Portanto, o código que executa o movimento fica depois do plano longo. Nas três
   respostas ele foi a string interrompida. A ordenação é um fator de fragilidade,
   não demonstração de que causou o limite nem solução suficiente por si só.
4. reasoning.effort=high está fixo no adapter. Na última resposta, 18.425 dos
   27.924 tokens de saída foram raciocínio. Reduzir só nomes de campos não limita
   essa parcela. Alterar o esforço pode afetar qualidade e precisaria de prova;
   não há evidência suficiente para prometer que medium resolveria.
5. Entrada textual cresceu: terceira chamada tem 119.757 bytes nos blocos de texto,
   mais 6.118 de instructions e 5.887 do schema. Entre as seções do contexto:
   skill 43.797 bytes, repertório 19.620, contrato criativo 12.830, request 11.995 e
   styles 10.018. Há oportunidade de selecionar instruções e transformar exemplos
   reutilizáveis em funções realmente disponíveis. Isso não autoriza remover
   referências/identidade nem prova esgotamento da janela do modelo.
6. O limite local de resposta é 4 MiB; os corpos tinham 325.612, 216.240 e 383.298
   bytes. O erro local correspondente a excesso seria outro. Todos foram recebidos
   e decodificados, sem evidência de corte pelo limite de bytes ou de timeout.
7. A reserva financeira passou no preflight. O erro de orçamento também seria
   outro. O teto acumulado US$ 4 não foi o gatilho registrado da interrupção.
8. Um retorno anterior do mesmo identificador gpt-6.1-sol, em
   reel-alternancia-20261110, tem status completed, 26.323 tokens de entrada e
   24.221 de saída. Isso comprova geração completa anterior, não aprovação visual
   ou estabilidade de todo o fluxo. A entrada atual é ~34% maior. Outra chamada
   anterior completou com total 64.708, contra hipótese de corte fixo em 64.000.

Código relevante: app/adapters/motion_ai.py, request_bytes (linha 165), payload
(linha 349) e classificação do retorno (linha 463); app/services/motion_effects.py,
preflight de custo; app/services/motion_orchestrator.py, passagem para imagem/render.

## Confronto com documentação oficial

A documentação diz que max_output_tokens limita tokens gerados incluindo os não
visíveis. reasoning_tokens já está incluído em output_tokens; não somar novamente.
[Counting tokens](https://developers.openai.com/api/docs/guides/token-counting).

O mesmo motivo max_output_tokens pode indicar teto de geração ou janela de
contexto. Logo, o rótulo não identifica sozinho qual limite efetivo interrompeu o
retorno. [Reasoning models](https://developers.openai.com/api/docs/guides/reasoning).

A página pública consultada para gpt-6.1-sol informa janela 1.050.000 e saída máxima
128.000. Os totais observados não explicam esgotamento desses limites públicos;
limites efetivos, comportamento do endpoint ou discrepância de contabilização
exigem investigação com IDs de requisição. Não inferir causa específica da conta.
[GPT-6.1 Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol).

A ordem das chaves do schema determina a ordem da saída estruturada, confirmando
o efeito observável de sort_keys=True, sem provar que trocar a ordem resolverá.
[Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs).

## Verificação executada nesta análise

Reproduzidos os três corpos salvos no parser real com httpx.MockTransport, sem
rede. Os três resultam em MOTION_AI_OUTPUT_LIMIT, preservando exatamente bytes,
usage e estimativa. Não houve tentativa de completar ou executar código truncado.
Artefatos: `.local/evals/motion-failure-audit-20261111/analysis.json`,
`parser-replay.json` e scripts de análise/replay na mesma pasta. IDs de provedor
constam do relatório local para investigação; sem credenciais. Nenhuma mensagem
foi enviada a terceiros. Sem CI global ou nova chamada ao modelo.

## Próximos passos recomendados, ainda não implementados

- Investigar a divergência do limite com os IDs e metadados já preservados; uma
  reprodução mínima futura precisa de orçamento específico, não de repetição da
  peça inteira. Não aumentar tokens às cegas nem trocar modelo por suposição.
- Separar serialização canônica para hash da serialização do schema de geração,
  definindo ordem deliberada. Não basta alterar a ordem de declarações no Python,
  pois sort_keys hoje a desfaz. Preservar snapshots existentes.
- Tornar a construção recuperável por artefato validado (plano e implementação),
  usando Temporal e persistência existentes. Não retomar string JSON arbitrária
  nem marcar resposta incompleta como sucesso. Uma eventual divisão em chamadas
  precisa de contrato/budget/identidade por efeito; não prometer menos custo.
- Reduzir código que o modelo precisa reescrever: mídia/seek e helpers reutilizáveis
  devem poder ser fornecidos pelo executor/bibliotecas. Manter direção visual e
  parâmetros livres; não remover moldura, fundo, objeto ou sincronismo para caber.
- Verificar localmente esses contratos, depois executar uma prova controlada.
  Os 234 testes anteriores verificaram conversão e validações; não eram uma prova
  de conclusão real pela API nem de qualidade visual.

As recuperações propostas antes desta investigação não partiram de uma causa
comprovada. A compactação mitigou volume, mas não deve ser descrita como correção
comprovada do bloqueio. Não há quarta tentativa autorizada e nenhum MP4 novo.
