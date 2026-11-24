# Video-reel v2 — reforço VR3 da Fatia A

Revisão imutável do business-video-reel-v1; v1 permanece disponível para replay.

Para cada text_element_id, beats cobre exatamente [scene.start_ms, scene.end_ms]: beats[0].phase=enter e beats[0].start_ms=scene.start_ms; beats[-1].phase=exit e beats[-1].end_ms=scene.end_ms. Beats contíguos, sem lacunas e com estados contínuos. Proibido hold com opacity=0, inclusive antes de enter ou depois de exit: hold exige start_state=end_state e opacity=1. Invisibilidade só via enter/exit; transform permanece visível (opacity=1) e desloca pelo menos 4px. CTA final mantém hold estável >=1500ms entre enter e exit. Não preencher pontas do timeline com holds fantasmas para adiar uma frase. Se a sequência de frases não couber nestas fronteiras, reformule a composição/plano dentro de VR1–VR3; não invente EDL nem mude a gravação.

O exemplo cta-plan.json passa o gate com hold de exatamente 1500ms.
Sem Fatia B ou aceite audiovisual.
