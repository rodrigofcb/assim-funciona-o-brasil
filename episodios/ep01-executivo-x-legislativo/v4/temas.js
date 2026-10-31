// Temas do ep. 1 v4. Selecionado por ?tema=night|day na URL (padrão night).
// `canvas` alimenta window.THEME (mapa3d.js e scene3d.js); `css` vira variáveis em :root.
window.TEMAS = {
  night: {
    canvas: {
      col:  { line: '176,186,198', w: '255,255,255', y: '255,223,0', g: '43,214,110', br: '255,236,120' },
      base: { fog: '255,255,255', fogA: 0, land: '176,186,198', water: '40,110,170', waterLine: '90,170,230', foot: '176,186,198',
              aMinor: .10, aMid: .36, aMajor: .70, aFoot: .12, aExtr: .40 },
      col3d:{ sub: '236,240,244', yes: '43,214,110', no: '229,50,45', dim: '176,186,198' },
      glow: { model: 0, lit: 0, pulse: 1.2, hl: 0, seat: .04 }
    },
    css: { bg: '#060E24', bgrgb: '6,14,36', ink: '#FFFFFF', inkrgb: '255,255,255', g: '#2BD66E', grgb: '43,214,110', y: '#FFDF00', yrgb: '255,223,0',
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
    css: { bg: '#F5F7FA', bgrgb: '245,247,250', ink: '#0B1630', inkrgb: '11,22,48', g: '#189648', grgb: '24,150,72', y: '#B8860B', yrgb: '184,134,11',
           r: '#D62828', bl: '#0B7FB3', dim: '82,92,108', vig: '20,30,50', vigA: .12, shadow: '0 2px 10px rgba(245,247,250,.9)' }
  }
};
(() => {
  const q = new URLSearchParams(location.search); const nome = (q.get('tema') in TEMAS) ? q.get('tema') : 'night';
  const T = TEMAS[nome]; window.THEME = T.canvas; window.TEMA = nome;
  document.documentElement.dataset.tema = nome;
  const R = document.documentElement.style; for (const k in T.css) R.setProperty('--' + k, T.css[k]);
})();
