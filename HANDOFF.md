# HANDOFF: Assim Funciona o Brasil (30/10/2026)

Contexto para continuar o trabalho em outra sessão. Fonte única: este repositório (https://github.com/rodrigofcb/assim-funciona-o-brasil, público; a sessão precisa de acesso de push e sempre faz commit e push). Sessão anterior: https://claude.ai/code/session_01QHFC48p8ATWcC9iW9vDkTt

## 1. Estado

- **Ep. 1 "Quem manda, o presidente ou o Congresso?" v3 está completo e renderizado**: `episodios/ep01-executivo-x-legislativo/v3/ep1_v3.mp4` (63,5 s, 1080×1920, trilha e efeitos mixados; commit `bd118b7`). Aguarda revisão do Rodrigo. Roteiro cena a cena com fontes em `episodios/ep01-executivo-x-legislativo/roteiro.md`.
- Série planejada (5 episódios sobre Legislativo × Executivo): 2) por que o Congresso tem duas casas; 3) deputado federal, estadual e vereador; 4) composição esquerda/centro/direita; 5) como acompanhar votações. Os episódios 2 a 5 ainda não começaram.
- Vinheta de abertura reutilizável (Brasil → Brasília → avião → Praça → local do tema) em `vinheta/` (8,5 s; `vinheta_v1.mp4`). O gancho do episódio deve estar na tela durante o mergulho.
- Canal: Instagram @assim_funciona_o_brasil; avatar escolhido `brand/avatar_D_verde_globo_sem_furo.png`.

## 2. Pipeline (tudo roda no container; Python 3 + Playwright/Chromium + ffmpeg)

Pasta de um episódio: `scene.html` (DOM + CSS, animações dirigidas por tempo), `timeline.js` (fonte única de tempos), `scene3d.js` (cenário 3D em canvas), `engine3d.js`, `mapa.js` (dados OSM locais).

```
python3 ferramentas/render_scenes.py <pasta> preview 1.2,3.4     # PNGs em <pasta>/preview/ para conferir layout
python3 ferramentas/render_scenes.py <pasta> full [cena]          # um MP4 por cena em out/, concatena em out/video.mp4 (lento: ~1 fps)
python3 ferramentas/sfx.py <pasta>                                # out/sfx.wav a partir de TL.sfx
python3 ferramentas/trilha.py <pasta> --bpm 72 --gain 0.7         # out/music.wav (violão amostrado, seções por beats)
ffmpeg -i out/music.wav -i out/sfx.wav -filter_complex "[1:a]asplit=2[s1][s2];[0:a]volume=-9dB[m];[m][s1]sidechaincompress=threshold=0.05:ratio=3:attack=10:release=300:makeup=1[md];[md][s2]amix=inputs=2:duration=longest:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[out]" -map "[out]" -ar 44100 out/mix.wav
ffmpeg -i out/video.mp4 -i out/mix.wav -map 0:v -map 1:a -c:v libx264 -crf 22 -preset slow -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart -shortest ep1_v3.mp4
ffmpeg -i ep1_v3.mp4 -vf scale=720:1280 -c:v libx264 -crf 24 -c:a copy preview_ep1_v3.mp4   # cópia de revisão
```

Regras do sistema:
- `timeline.js` precisa continuar parseável como JSON depois de tirar `window.TL =` (Python faz isso). Campos: `fps, end, scenes, handoff, zoom` (câmera log-altitude norte-para-cima antes do handoff), `cam` (keyframes `[t, px,py,pz, tx,ty,tz, fov, up|null]`), `beats`, `build`, `hl`, `travel`, `sfx` (`[beat, tipo, opts]`; tipos: tick, pop, impact, thrum, whoosh, sweep, fill), `fill`, `riser`, `music_in`.
- Cada beat vira `--b-<nome>` no `:root`; elementos com `data-in`/`data-out` recebem `--in`/`--out`. `window.seek(ms)` chama `draw3d(t)` antes de posicionar as animações (ordem importa para elementos recém-exibidos).
- Contadores animados: `.num` com `--to` inline; keyframes gerados por elemento; `@property --n` tem `inherits:true` (o `::after` precisa herdar).
- Rótulos pinados a pontos 3D: `.pin` (ministérios) e `.lab` (`data-key` = âncora em `scene3d.js`, `data-from`/`data-to` = beats); a posição x é limitada à tela.
- Render em segundo plano com `nohup ... > render.log &` e acompanhar o log; nunca `sleep` encadeado.
- Coordenadas: projeção azimutal equidistante centrada no Congresso (lat −15,7997, lon −47,8644), metros, x leste, y norte, z para cima. Eixo Monumental vai do Congresso (0,0) à Torre de TV (−3060, 997). Planalto (399, 62), STF (265, −280), ministérios em x −300…−920.

## 3. Direção de arte (decisões firmes do Rodrigo)

- Sem narração; texto grande na tela; cada animação com efeito sonoro sincronizado; nada de animação decorativa sem significado (ex.: barras que não representam nada).
- Mundo 3D em blueprint sobre o mapa real de Brasília (OSM + Natural Earth), prédios com linhas arquitetônicas reais; ícones só em momentos pontuais.
- Simbolismo de Brasília como pano de fundo de todos os vídeos (avião, cabine = Praça dos Três Poderes, "o avião só decola com todos a bordo"); sem giro de câmera.
- Cores: verde = Executivo / "com o governo"; amarelo = Legislativo / "sim"; azul-claro do blueprint = "não" / "contra"; vermelho = esquerda, roxo = centro, azul (diferente do da bandeira) = direita (reservados para o ep. 4).
- Tipografia: espaço entre palavras explícito (`word-spacing`) porque o kerning apertado deixava as palavras coladas; títulos no topo.
- Música: violão clássico brasileiro, cue original composta por cena (`ferramentas/trilha.py`), mais baixa que os efeitos, com ducking; assinatura melódica (subida cromática, salto de terça, repouso) em "Os dois" e no fecho.
- A transição geométrica inspirada em Athos Bulcão foi **retirada** do ep. 1 (não combinou); a lógica modular pode voltar em outro contexto, nunca azulejos literais.
- Sempre citar as fontes na tela quando houver números.

## 4. Dados e fontes

- `dados/politicometro_2026-10-30.md`: números coletados em politicometro.org (composição do Congresso hoje e em fev/2027 por partido e bloco, base aliada 345/63/86 em 1.148 votações, PLP 281/2019 252×176 com quórum 257, atividade do Plenário, transparência municipal, regras constitucionais). `dados/congresso_composicao.json` tem a composição completa.
- Crédito combinado: "dados: Câmara dos Deputados (ou Câmara, Senado e TSE), via Politicômetro (politicometro.org)". Blocos ideológicos usam a classificação de Bolognesi, Ribeiro e Codato (2023); UNIÃO, PRD e MISSÃO ficam "sem nota".
- politicometro.org bloqueia acesso de fora do Brasil: só abre pelo navegador do app (ponte com o Mac), com aprovação a cada carregamento; dentro da página, `fetch()` para `/api/plenario` e outras rotas evita novas aprovações. O site anuncia acesso para assistentes (MCP) "em breve".
- Números para os próximos episódios: ep. 3 → 81 senadores, 513 deputados federais, 1.015 estaduais, 58.124 vereadores, 11.027 prefeitos e vices (70.804 eleitos); ep. 4 → Câmara hoje 116 E / 11 C / 332 D / 54 sem nota, Senado 17 / 0 / 60 / 4, e a legislatura de 2027 (PL de 98 para 121 deputados e de 15 para 28 senadores); ep. 5 → 1.458 votações no Plenário em 2026, 3.788 das 5.569 cidades sem dados abertos, 17% das Câmaras Municipais publicam presença e votos.

## 5. Licenças e créditos obrigatórios

- Mapa: © OpenStreetMap contributors (ODbL); fronteiras: Natural Earth (domínio público).
- Violão: amostras FluidR3 (Frank Wen), CC BY 3.0 (`musica/CREDITOS.md`).
- `musica/midi/`: 20 MIDIs de obras em domínio público baixados do MuseScore (tabela no README); "Odeon" é harmonização de terceiro (Rolf Steyer) e não pode ir a público sem substituição.
- Google Maps/Earth não podem ser reestilizados; painéis de Athos Bulcão são protegidos (só o princípio, nunca cópias); textos e design do Politicômetro são reservados, os números são de fontes públicas.

## 6. Pendências e ideias

- Revisão do Rodrigo do ep. 1 v3 (ritmo da cena 3, legibilidade do hemiciclo no celular, níveis de áudio).
- Ressalvas de conteúdo do ep. 1: o PLP 281/2019 é lei complementar (por isso 257); lei ordinária passa por maioria simples dos presentes, e o vídeo não explica a diferença. Os "19 sem classificação" são o resto dos 513 fora dos três grupos do Politicômetro; critério exato desconhecido.
- Ep. 2 em diante: reutilizar a vinheta e o mundo 3D; hemiciclo (`scene3d.js`) já serve para composição por bloco (ep. 4) e para as duas casas (ep. 2, com 81 assentos para o Senado).
- Música: continuar a biblioteca PD; substituir Odeon; testar valsas para fechos; decidir se a assinatura melódica vira identidade sonora do canal.
- Ideia arquivada: vídeo próprio sobre o simbolismo de Brasília.

## 7. Preferências de trabalho do Rodrigo

Respostas curtas em português, um passo por vez, sem travessão (usar ponto e vírgula), questionar premissas; prefere ver prévias (frames ou cópia 720p) antes de decidir; commit e push a cada etapa; vídeos grandes: a ponte com o Mac aceita no máximo 30 MB por arquivo, então o master vai pelo cartão do chat ou pelo GitHub.
