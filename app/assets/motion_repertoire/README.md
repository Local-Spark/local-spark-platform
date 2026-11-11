# Repertório selecionado para a prova de Reel

`business-reel-v1` é uma curadoria explícita, não um estilo padrão por negócio.
A seleção usa o campo opcional `repertoire_id` do pedido existente. Sem seleção,
o campo não é serializado e pedidos/snapshots anteriores mantêm seu conteúdo.
Nenhuma seleção ativa execução, orçamento ou envio por conta própria.

O [manifesto](business-reel-v1/manifest.json) registra origem, versão, hashes,
permissão/limitações, mecanismo e contexto de uso de cada item. O carregador
verifica o manifesto, os exemplos, os avisos de licença e as imagens. Modificar
uma versão publicada exige outro ID; não atualizar hashes para reescrever um
pedido histórico.

## O que o modelo recebe

- Três exemplos completos de código adaptável: composição com evidência
  (Maestro), percurso com ações em estações (Finalizador S16) e tipografia em
  camadas (claude-video). São funções que podem integrar `scene_init`; o modelo
  recebe os bytes do código, a finalidade, os limites e os avisos de licença.
- Seis JPEGs já extraídos nas análises anteriores, copiados sem transformação:
  Lucas Leite em aproximadamente 3, 5 e 27 s; Felipe Borges em 25,75, 30,25 e
  35,25 s. Rótulos identificam fonte, sequência, instante aproximado e hash.
- APIs dos runtimes `MotionV1` e `MotionElementsV1`, já presentes no contrato
  criativo. Os exemplos exigem as versões/hashes capturados desses runtimes.

Os quadros de Lucas mostram planos de escala/foco diferentes e um card composto
ao lado da pessoa. Os de Felipe mostram passagem de atenção entre estados e
aprofundamento de uma etapa. Essas amostras não comprovam curva exata, fluidez
integral, sincronismo ou áudio. Não usar tecnologia, cores, rostos ou textos
das referências como identidade ou conteúdo do negócio.

## Separação de uso

As imagens entram apenas como `finish_reference_only` no pedido ao modelo.
Não recebem IDs `assets/`, não entram no bundle do renderer e não são evidência
da peça em `source/current/previous`. Os vídeos completos permanecem locais.
A indicação pelo titular autoriza o uso de referência nesta prova privada;
não foi declarada licença para reutilizar essas imagens na peça ou distribuí-las
como acervo. Código e avisos de licença têm proveniência separada no manifesto.

Os exemplos não são bibliotecas instaladas automaticamente. A implementação da
peça deve incorporar/adaptar a função necessária e integrá-la ao seek do vídeo.
Somente os runtimes existentes são prefixados pelo renderer; não foram adicionados
Remotion, GSAP, imports ou rede. O código do exemplo não é prova de acabamento.

## Integração e verificação local

Fluxo: seleção no `MotionRequest` → `MotionContext.capture` →
`MotionInputLoader.prepare` → `MotionModelRequest.reference_images` →
`OpenAIMotionProvider.build_request`. O mesmo corpo multimodal passa pela contagem
e pelos tetos de tokens/custo existentes antes de qualquer futura chamada.
Não foi executada contagem remota nesta implementação.

Limites locais adicionais: 64 KiB de texto expandido, até oito imagens,
1 MiB por imagem e 4 MiB no conjunto. A v1 tem 19.916 bytes de contexto textual
na serialização padrão JSON e 132.720 bytes de imagens. Isso não é contagem de
tokens nem estimativa de custo. O teto de corpo do adaptador também permanece.

Verificação sem provedor ou render:

```sh
.venv/bin/pytest -q app/tests/unit/test_motion_repertoire.py
node --test app/tests/node/motion_repertoire.test.cjs
```

O teste Node executa as funções com os runtimes reais e DOM/Canvas substituídos,
verificando busca temporal repetida/reversa. Não produz quadros nem vídeo.
A etapa 3 acrescentou direção fornecida antes da construção; a etapa 4 passou a
transmitir orientações e dois exemplos adicionais na skill `instagram-reel-v3`.
Este pacote v1 permanece intacto. A etapa 6 exportará a entrada integral usando
os montadores do produto. Não tratar esta curadoria como prompt final exportado.
