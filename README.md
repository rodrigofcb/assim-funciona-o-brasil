# Assim Funciona o Brasil

Vídeos curtos (9:16, 1080×1920) de educação política em motion graphics, com linguagem acessível e sem termos técnicos.

Instagram: @assim_funciona_o_brasil

## Estrutura

- `brand/` identidade visual: avatar, paleta, script que gera o avatar.
- `episodios/epNN-slug/` um diretório por vídeo: `roteiro.md`, `scene.html` (cenas animadas em HTML/CSS), `render.py` (frames via Chromium headless), `music.py` (trilha procedural), MP4 final.
- `vozes/` modelo de voz do Piper para narração em pt-BR (ver README da pasta).

## Paleta

| Uso | Cor |
|---|---|
| Fundo (azul da bandeira, escurecido) | `#08204F` |
| Verde (Executivo) | `#00953A` |
| Amarelo (Legislativo, destaques) | `#FFDF00` |
| Esquerda | `#E03A3E` |
| Centro | `#8A4DE8` |
| Direita (azul diferente do da bandeira) | `#2F8BEF` |

Tipografia: Inter Display (títulos, peso 800–900) e Inter (texto).

## Como renderizar um episódio

```bash
cd episodios/ep01-executivo-x-legislativo
python3 music.py            # gera music.wav
python3 render.py full      # gera frames/f0000.png ... a 30 fps
ffmpeg -framerate 30 -i frames/f%04d.png -i music.wav -c:v libx264 -pix_fmt yuv420p -crf 18 -c:a aac -shortest saida.mp4
```

Dependências: Python 3 com `playwright` (Chromium instalado), `numpy`, `scipy`, `pillow`; `ffmpeg`.

## Convenções dos vídeos

- 45 a 60 segundos por episódio; gancho nos primeiros 5 s; última cena puxa o próximo.
- Legendas sincronizadas com a narração, dentro da zona segura (nada abaixo de y=1760).
- As animações são dirigidas pelo tempo (`seek(ms)` em `scene.html`), o que permite render frame a frame e sincronia exata com o áudio.

## Série 1: o Legislativo

1. Quem manda, o presidente ou o Congresso? (Executivo × Legislativo)
2. As duas casas: Câmara e Senado, e por que o Congresso é a soma das duas
3. Deputado federal, deputado estadual e vereador: quem cuida do quê
4. Quem está lá hoje: esquerda, centro e direita em cada casa
5. Como acompanhar o que eles votam
