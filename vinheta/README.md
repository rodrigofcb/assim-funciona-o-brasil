# Vinheta de abertura

Conceito (Rodrigo): somos uma nação soberana e definida por fronteiras claras, somos um Brasil; no meio do Brasil
está o centro administrativo, Brasília, de onde decola um avião cujo cockpit é a Praça dos Três Poderes.
Todo vídeo abre assim e segue até o lugar que é o foco do tema (a Praça, um estado, uma capital).

Camadas e escalas (altitude da câmera):
- país: fronteira do Brasil, estados, vizinhos e capitais (Natural Earth, domínio público) — some abaixo de ~40 km
- Brasília inteira: limite do DF + vias principais e Lago Paranoá (`aviao.js`, do OSM) — de ~160 km a ~4 km
- Praça/Esplanada: detalhe do OSM (`../episodios/.../v3/mapa.js`) — abaixo de ~20 km

Câmera em `timeline.js` → `zoom`: [t, alvo x, alvo y, altitude, pitch, rumo]. Altitude interpola em escala log;
o alvo se aproxima proporcionalmente à altitude, para o destino final ficar parado na tela.
Projeção de todos os dados: azimutal equidistante centrada no Congresso (metros), ver `ferramentas/brasil_ne.py`.
