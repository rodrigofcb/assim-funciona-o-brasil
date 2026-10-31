# Marca e temas

- `avatar_*.svg/png`: opções de avatar do perfil (`make_avatar*.py` geram). Em uso: `avatar_D_verde_globo_sem_furo.png`.
- `temas.js`: temas visuais reutilizáveis para os vídeos. A cena carrega `brand/temas.js` e escolhe o tema por `?tema=`:
  - `night` (padrão): CAD escuro, azul-marinho quase preto, linhas cinza, texto branco.
  - `day`: CAD impresso, papel quase branco, linhas ardósia, texto azul-marinho; verde e amarelo escurecidos para ler sobre branco.
  - `alvorada`: blueprint azul (o azul do ep. 1 v3) com as regras da v4 (sem brilho permanente, base rala, texto branco).

Render com tema: `TEMA=day python3 ferramentas/render_scenes.py <pasta> full` (saídas em `out-day/`, `preview-day/`) e
`TEMA=day bash episodios/<ep>/v4/render_all.sh` (master `ep1_v4-day.mp4`). Sem `TEMA`, usa `night`.

Para um episódio novo: carregar `brand/temas.js` antes de `vinheta/mapa3d.js`, usar só as variáveis CSS (`--bg`, `--ink`, `--g`, `--y`, …)
e as cores de `window.THEME` no canvas; nenhuma cor fixa no HTML ou no JS da cena.
