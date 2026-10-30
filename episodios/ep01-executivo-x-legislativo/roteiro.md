# Ep. 1: Quem manda, o presidente ou o Congresso?

## v3 (atual): texto na tela, sem narração, mundo 3D em blueprint sobre o mapa real

Duração: 63,5 s. Arquivo: `v3/ep1_v3.mp4` (1080×1920) e `v3/preview_ep1_v3.mp4` (720p, para revisão). Linha do tempo única em `v3/timeline.js` (câmera, beats, efeitos); cenário em `v3/scene3d.js`; trilha original por cena em `ferramentas/trilha.py`; efeitos em `ferramentas/sfx.py`.

| cena | tempo | na tela | fonte |
|---|---|---|---|
| 1 | 0–10,4 s | "Quem manda no Brasil? o presidente ou o Congresso?" sobre o mergulho Brasil → Brasília → avião → Praça; Planalto acende verde, Congresso amarelo, STF se desenha | mapa OSM + Natural Earth |
| 2 | 10,4–25,5 s | "Os dois. Mas em coisas diferentes." Executivo administra: dinheiro, obras, serviços (ministérios acendem na Esplanada). Legislativo cria as regras e fiscaliza (holofote varre a Esplanada) | |
| 3 | 25,5–36,9 s | "Uma lei precisa dos dois." O documento viaja Congresso → Planalto (aprova; sanciona… ou veta) e volta (pode derrubar o veto). "Para derrubar um veto: 257 deputados + 41 senadores; metade mais um de cada casa" | CF art. 66 §4 |
| 4 | 36,9–48,6 s | "Mas maioria nem sempre basta." Hemiciclo de 513 assentos no gramado da Esplanada: 252 sim (amarelo), 176 não (azul-claro), linha "precisava de 257", carimbo REJEITADO, "faltaram 5 votos". Caso: PLP 281/2019 (regras para bancos em crise), Câmara, 14/10/2026 | Câmara dos Deputados, via Politicômetro |
| 5 | 48,6–58,8 s | "Então, quem manda? Em 1.148 votações da Câmara desde 2023: 345 votam com o governo (verde), 63 dividem (contorno branco), 86 votam contra (azul-claro), 19 sem classificação." Resposta: "O presidente governa com a maioria que constrói no Congresso." | critério e dados: Politicômetro (votações nominais, mar/2023–out/2026) |
| 6 | 58,8–63,5 s | Câmera sobe de volta ao avião; marca, @assim_funciona_o_brasil, "próximo episódio: por que o Congresso tem duas casas?", créditos | |

Créditos na tela (cena 6): dados: Câmara dos Deputados, via Politicômetro · mapa © OpenStreetMap contributors · fronteiras Natural Earth · violão: amostras FluidR3 (Frank Wen, CC BY 3.0) · trilha e efeitos originais.

Cores: verde = Executivo / "com o governo"; amarelo = Legislativo / "sim"; azul-claro (cor das linhas do blueprint) = "não" / "contra"; vermelho, roxo e azul ficam reservados para esquerda, centro e direita (ep. 4).

Decisões: a transição geométrica inspirada em Athos Bulcão foi retirada deste episódio (não combinava); o rodapé com o crédito do mapa some na cena 3 e volta nos créditos finais.

## v1 (arquivada): narração

Duração: 68 s. `ep1_final.mp4` renderizado com narração do Rodrigo (opção A: só acabamento), trilha procedural com ducking e legendas sincronizadas.

Áudio: `audio/narracao_bruta.wav` (gravação do celular) → `ferramentas/voz.py` → `audio/narracao_A_acabamento.wav` → mix com `music.wav` em `audio/mix_final.wav`. Tempos das cenas ajustados em `sync.py` a partir da gravação.

Cena 1 (0–5 s): "Quem manda no Brasil: o presidente ou o Congresso?"
Cena 2 (5–16 s): "Os dois, mas em coisas diferentes. O Executivo, que é presidente, governador e prefeito, administra: dinheiro, obras, serviços. O Legislativo cria as regras e fiscaliza quem administra."
Cena 3 (16–30 s): "Nenhum dos dois faz lei sozinho. O presidente pode propor uma lei, mas quem aprova é o Congresso. O Congresso pode aprovar uma lei, mas o presidente pode vetar. E o Congresso ainda pode derrubar o veto."
Cena 4 (30–40 s): "Com o dinheiro é igual: o governo propõe o orçamento, o Congresso decide onde cada real vai." (simplificação: emendas não entram)
Cena 5 (40–50 s): "Por isso você ouve falar em base aliada: o governo precisa de maioria no Congresso para aprovar o que quer. Sem maioria, trava."
Cena 6 (50–55 s): "Mas o Congresso não é um lugar só. São dois. É o próximo vídeo."
