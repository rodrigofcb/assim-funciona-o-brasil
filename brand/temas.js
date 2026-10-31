// Temas visuais do canal (reutilizáveis em qualquer episódio). Selecionado por ?tema=night|day|alvorada na URL (padrão night).
// `canvas` alimenta window.THEME (vinheta/mapa3d.js e scene3d.js do episódio); `css` vira variáveis --nome em :root.
//   night    = CAD escuro: azul-marinho quase preto, linhas cinza, texto branco (ep. 1 v4)
//   day      = CAD impresso: papel quase branco, linhas ardósia, texto azul-marinho
//   alvorada = blueprint azul (o azul da v3), com as lições da v4: sem brilho permanente, base rala, texto branco
// Chaves css: bg/bgrgb (fundo), bgimg (gradiente opcional do palco), ink/inkrgb (texto), g/grgb, y/yrgb, r, bl (cores com significado),
//   dim (assento vazio), vig/vigA (vinheta), shadow (sombra curta das etiquetas).
window.TEMAS = {
  night: {
    canvas: {
      col:  { line: '176,186,198', w: '255,255,255', y: '255,223,0', g: '43,214,110', br: '255,236,120' },
      base: { fog: '255,255,255', fogA: 0, land: '176,186,198', water: '40,110,170', waterLine: '90,170,230', foot: '176,186,198',
              aMinor: .10, aMid: .36, aMajor: .70, aFoot: .12, aExtr: .40 },
      col3d:{ sub: '236,240,244', yes: '43,214,110', no: '229,50,45', dim: '176,186,198' },
      glow: { model: 0, lit: 0, pulse: 1.2, hl: 0, seat: .04 }
    },
    css: { bg: '#060E24', bgrgb: '6,14,36', bgimg: 'none', ink: '#FFFFFF', inkrgb: '255,255,255', g: '#2BD66E', grgb: '43,214,110', y: '#FFDF00', yrgb: '255,223,0',
           r: '#E5322D', bl: '#38D6FF', dim: '176,186,198', vig: '0,0,0', vigA: .5, shadow: '0 4px 16px rgba(0,0,0,.8)' }
  },
  day: {
    canvas: {
      col:  { line: '82,92,108', w: '11,22,48', y: '204,150,0', g: '24,150,72', br: '204,150,0' },
      base: { fog: '255,255,255', fogA: 0, land: '40,60,100', water: '40,110,170', waterLine: '40,110,170', foot: '82,92,108',
              aMinor: .14, aMid: .40, aMajor: .80, aFoot: .14, aExtr: .45, border: '11,22,48', borderW: 3 },
      col3d:{ sub: '11,22,48', yes: '24,150,72', no: '214,40,40', dim: '82,92,108' },
      glow: { model: 0, lit: 0, pulse: 1.2, hl: 0, seat: .04 }
    },
    css: { bg: '#F5F7FA', bgrgb: '245,247,250', bgimg: 'none', ink: '#0B1630', inkrgb: '11,22,48', g: '#189648', grgb: '24,150,72', y: '#B8860B', yrgb: '184,134,11',
           r: '#D62828', bl: '#0B7FB3', dim: '82,92,108', vig: '20,30,50', vigA: .12, shadow: '0 2px 10px rgba(245,247,250,.9)' }
  },
  alvorada: {
    canvas: {
      col:  { line: '184,228,255', w: '255,255,255', y: '255,223,0', g: '43,214,110', br: '255,236,120' },
      base: { fog: '70,120,220', fogA: .14, land: '120,180,255', water: '80,150,255', waterLine: '120,190,255', foot: '120,180,255',
              aMinor: .12, aMid: .34, aMajor: .65, aFoot: .14, aExtr: .40 },
      col3d:{ sub: '225,238,255', yes: '43,214,110', no: '240,62,56', dim: '184,228,255' },
      glow: { model: 0, lit: 0, pulse: 1.2, hl: 0, seat: .05 }
    },
    css: { bg: '#0A2256', bgrgb: '10,34,86', bgimg: 'radial-gradient(110% 70% at 50% 35%, #12398F 0%, #0C2868 40%, #071A48 75%, #051236 100%)',
           ink: '#FFFFFF', inkrgb: '255,255,255', g: '#2BD66E', grgb: '43,214,110', y: '#FFDF00', yrgb: '255,223,0',
           r: '#F03E38', bl: '#38D6FF', dim: '184,228,255', vig: '0,0,0', vigA: .45, shadow: '0 4px 16px rgba(0,0,0,.8)' }
  }
};
(() => {
  const q = new URLSearchParams(location.search); const nome = (q.get('tema') in TEMAS) ? q.get('tema') : 'night';
  const T = TEMAS[nome]; window.THEME = T.canvas; window.TEMA = nome;
  document.documentElement.dataset.tema = nome;
  const R = document.documentElement.style; for (const k in T.css) R.setProperty('--' + k, T.css[k]);
})();
