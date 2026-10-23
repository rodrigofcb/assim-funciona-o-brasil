"""Re-sincroniza scene.html com a narração gravada (Video_1_todas_as_cenas.wav).

Tempos do vídeo = tempo bruto da gravação - OFFSET (3.0 s), de modo que o bloco 1 comece em 0.7 s.
Cada substituição abaixo precisa casar exatamente uma vez; se o HTML mudar, o script avisa.
"""
import pathlib, re, sys

p = pathlib.Path(__file__).parent / "scene.html"
s = p.read_text(encoding="utf-8")

R = [
 # linha do tempo
 ("window.T = { s1: 0, s2: 5, s3: 16, s4: 30, s5: 40, s6: 50.5, end: 56.5 };",
  "window.T = { s1: 0, s2: 4.6, s3: 20.4, s4: 37.8, s5: 46.8, s6: 58.8, end: 68 };"),
 # cena 1
 ("#cardL{left:70px;animation:slideL .8s var(--over) 1.2s both}#cardR{left:590px;animation:slideR .8s var(--over) 1.8s both}",
  "#cardL{left:70px;animation:slideL .8s var(--over) 2.05s both}#cardR{left:590px;animation:slideR .8s var(--over) 3.3s both}"),
 ("#cardL .in{animation:bumpL .55s var(--ease) 3.3s both}#cardR .in{animation:bumpR .55s var(--ease) 3.3s both}",
  "#cardL .in{animation:bumpL .55s var(--ease) 3.85s both}#cardR .in{animation:bumpR .55s var(--ease) 3.85s both}"),
 ("animation:pop .6s var(--over) 1.55s both}", "animation:pop .6s var(--over) 3.15s both}"),
 ("#ou .t{animation:ouPulse .55s var(--ease) 3.3s both}", "#ou .t{animation:ouPulse .55s var(--ease) 3.85s both}"),
 # cena 2
 ("#exec{top:150px;animation:pop .7s var(--over) calc(var(--s2) + .45s) both}", "#exec{top:150px;animation:pop .7s var(--over) calc(var(--s2) + 3.3s) both}"),
 ("calc(var(--s2) + .8s) both}", "calc(var(--s2) + 4.5s) both}"),
 ("calc(var(--s2) + 3.9s) both}", "calc(var(--s2) + 7.2s) both}"),
 ("calc(var(--s2) + 1.05s) both}", "calc(var(--s2) + 11s) both}"),
 ("calc(var(--s2) + 1.4s) both}", "calc(var(--s2) + 11.4s) both}"),
 ("#c1{animation-delay:calc(var(--s2) + 4.6s)}#c2{animation-delay:calc(var(--s2) + 5.3s)}#c3{animation-delay:calc(var(--s2) + 6s)}",
  "#c1{animation-delay:calc(var(--s2) + 8.1s)}#c2{animation-delay:calc(var(--s2) + 9.05s)}#c3{animation-delay:calc(var(--s2) + 9.55s)}"),
 ("#c4{animation-delay:calc(var(--s2) + 7.6s)}#c5{animation-delay:calc(var(--s2) + 8.6s)}",
  "#c4{animation-delay:calc(var(--s2) + 12.5s)}#c5{animation-delay:calc(var(--s2) + 13.7s)}"),
 ("animation:lupaGo 2.4s var(--ease) calc(var(--s2) + 9s) both}", "animation:lupaGo 1.6s var(--ease) calc(var(--s2) + 13.9s) both}"),
 ("T.s2+1.7+k*0.025", "T.s2+11.7+k*0.02"),
 ('style="--t:var(--s2);--d:2.6s"', 'style="--t:calc(var(--s2) + .3s);--d:2.7s"'),
 ('style="--t:calc(var(--s2) + 2.6s);--d:4.2s"', 'style="--t:calc(var(--s2) + 3.3s);--d:7.2s"'),
 ('style="--t:calc(var(--s2) + 6.8s);--d:4.2s"', 'style="--t:calc(var(--s2) + 10.9s);--d:4.6s"'),
 # cena 3
 ("#s3 .l1{animation-delay:calc(var(--s3) + .2s)}#s3 .l2{animation-delay:calc(var(--s3) + .45s);",
  "#s3 .l1{animation-delay:calc(var(--s3) + .3s)}#s3 .l2{animation-delay:calc(var(--s3) + .55s);"),
 ("calc(var(--s3) + .7s) both}", "calc(var(--s3) + .8s) both}"),
 ("calc(var(--s3) + 1s) both}", "calc(var(--s3) + 1.1s) both}"),
 ("animation:docPop .6s var(--over) calc(var(--s3) + 1.5s) both, docMove 12.5s var(--ease) calc(var(--s3) + 1.5s) both}",
  "animation:docPop .6s var(--over) calc(var(--s3) + 3.9s) both, docMove 12s var(--ease) calc(var(--s3) + 3.9s) both}"),
 ("@keyframes docMove{0%{transform:translateY(505px)}20%{transform:translateY(505px)}26.4%{transform:translateY(1205px)}48%{transform:translateY(1205px)}54.4%{transform:translateY(505px)}72%{transform:translateY(505px)}78.4%{transform:translateY(1205px)}100%{transform:translateY(1205px)}}",
  "@keyframes docMove{0%{transform:translateY(505px)}16.67%{transform:translateY(505px)}21.67%{transform:translateY(1205px)}58.33%{transform:translateY(1205px)}63.33%{transform:translateY(505px)}86.67%{transform:translateY(505px)}91.67%{transform:translateY(1205px)}100%{transform:translateY(1205px)}}"),
 ("stampIn .4s var(--over) calc(var(--s3) + 5s) both, fadeOut .3s linear calc(var(--s3) + 8.5s) forwards}",
  "stampIn .4s var(--over) calc(var(--s3) + 6.6s) both, fadeOut .3s linear calc(var(--s3) + 12.3s) forwards}"),
 ("animation-delay:calc(var(--s3) + 8.5s)}", "animation-delay:calc(var(--s3) + 12.3s)}"),
 ("animation:draw .35s var(--ease) calc(var(--s3) + 11.5s) both}", "animation:draw .35s var(--ease) calc(var(--s3) + 15.2s) both}"),
 ("animation-delay:calc(var(--s3) + 11.6s)}", "animation-delay:calc(var(--s3) + 15.4s)}"),
 ("#tg1{top:765px;--t:calc(var(--s3) + 1.7s);--d:2.3s}", "#tg1{top:765px;--t:calc(var(--s3) + 4.2s);--d:1.6s}"),
 ("#tg2{top:1125px;--t:calc(var(--s3) + 5s);--d:2.5s}", "#tg2{top:1125px;--t:calc(var(--s3) + 6.4s);--d:1.6s}"),
 ("#tg3{top:765px;--t:calc(var(--s3) + 8.5s);--d:2s}", "#tg3{top:765px;--t:calc(var(--s3) + 12.2s);--d:1.4s}"),
 ("#tg4{top:1125px;--t:calc(var(--s3) + 11.5s);--d:2.6s}", "#tg4{top:1125px;--t:calc(var(--s3) + 15.2s);--d:1.9s}"),
 ('style="--t:var(--s3);--d:2.5s"', 'style="--t:calc(var(--s3) + .4s);--d:2.9s"'),
 ('style="--t:calc(var(--s3) + 2.5s);--d:4s"', 'style="--t:calc(var(--s3) + 3.7s);--d:4.3s"'),
 ('style="--t:calc(var(--s3) + 6.5s);--d:3.5s"', 'style="--t:calc(var(--s3) + 8.3s);--d:4.8s"'),
 ('style="--t:calc(var(--s3) + 10s);--d:3.8s"', 'style="--t:calc(var(--s3) + 13.6s);--d:3.3s"'),
 # cena 4
 ("#s4 .l1{animation-delay:calc(var(--s4) + .2s)}", "#s4 .l1{animation-delay:calc(var(--s4) + .3s)}"),
 ("calc(var(--s4) + .6s) both}", "calc(var(--s4) + .7s) both}"),
 ("calc(var(--s4) + .9s) both}", "calc(var(--s4) + 1s) both}"),
 ("coinsMove .8s var(--ease) calc(var(--s4) + 3.3s) both, fadeOut .4s linear calc(var(--s4) + 4.6s) forwards}",
  "coinsMove .8s var(--ease) calc(var(--s4) + 4.9s) both, fadeOut .4s linear calc(var(--s4) + 5.9s) forwards}"),
 ("#co1{top:90px;animation-delay:calc(var(--s4) + .9s)}#co2{top:50px;animation-delay:calc(var(--s4) + 1.4s)}#co3{top:10px;animation-delay:calc(var(--s4) + 1.9s)}",
  "#co1{top:90px;animation-delay:calc(var(--s4) + 2.7s)}#co2{top:50px;animation-delay:calc(var(--s4) + 3.1s)}#co3{top:10px;animation-delay:calc(var(--s4) + 3.5s)}"),
 ("animation:cap 2s linear calc(var(--s4) + 1.9s) both}", "animation:cap 2s linear calc(var(--s4) + 3.5s) both}"),
 ("(T.s4+4.8+i*.45)", "(T.s4+5.8+i*.4)"),
 ("(T.s4+5+i*.45)", "(T.s4+6+i*.4)"),
 ('style="--t:var(--s4);--d:3.5s"', 'style="--t:calc(var(--s4) + .4s);--d:4.2s"'),
 ('style="--t:calc(var(--s4) + 3.5s);--d:6.2s"', 'style="--t:calc(var(--s4) + 4.7s);--d:4s"'),
 # cena 5
 ("#s5 .l1{animation-delay:calc(var(--s5) + .2s)}", "#s5 .l1{animation-delay:calc(var(--s5) + 2.3s)}"),
 ("animation:pop .6s var(--over) calc(var(--s5) + .6s) both}", "animation:pop .6s var(--over) calc(var(--s5) + 2.7s) both}"),
 ("#meio{left:535px;top:470px;width:10px;height:520px;border-left:10px dashed var(--amarelo);animation:pop .4s var(--ease) calc(var(--s5) + 4.8s) both}",
  "#meio{left:535px;top:470px;width:10px;height:520px;border-left:10px dashed var(--amarelo);animation:pop .4s var(--ease) calc(var(--s5) + 5.6s) both}"),
 ("color:var(--amarelo);animation:pop .4s var(--ease) calc(var(--s5) + 4.8s) both}", "color:var(--amarelo);animation:pop .4s var(--ease) calc(var(--s5) + 5.6s) both}"),
 ("animation:pop .5s var(--over) calc(var(--s5) + 5.3s) both, fadeOut .3s linear calc(var(--s5) + 7.5s) forwards}",
  "animation:pop .5s var(--over) calc(var(--s5) + 6.4s) both, fadeOut .3s linear calc(var(--s5) + 8.9s) forwards}"),
 ("animation:stampIn .45s var(--over) calc(var(--s5) + 7.9s) both;--r:-6deg}", "animation:stampIn .45s var(--over) calc(var(--s5) + 10.35s) both;--r:-6deg}"),
 ("(T.s5+.3+i*.006)", "(T.s5+.5+i*.006)"),
 ("(T.s5+2.6+i*.022)", "(T.s5+4.3+i*.022)"),
 ("(T.s5+7.6+(maj-i)*.03)", "(T.s5+9.1+(maj-i)*.03)"),
 ('style="--t:var(--s5);--d:3.5s"', 'style="--t:calc(var(--s5) + .4s);--d:3.2s"'),
 ('style="--t:calc(var(--s5) + 3.5s);--d:4s"', 'style="--t:calc(var(--s5) + 4s);--d:4.6s"'),
 ('style="--t:calc(var(--s5) + 7.5s);--d:3s"', 'style="--t:calc(var(--s5) + 8.9s);--d:2.7s"'),
 # cena 6
 ("#g6bowl{animation:bowlGo 1s var(--over) calc(var(--s6) + .9s) both}", "#g6bowl{animation:bowlGo 1s var(--over) calc(var(--s6) + 2.7s) both}"),
 ("#g6dome{animation:domeGo 1s var(--over) calc(var(--s6) + .9s) both}", "#g6dome{animation:domeGo 1s var(--over) calc(var(--s6) + 2.7s) both}"),
 ("animation:pop .5s var(--over) calc(var(--s6) + 1.7s) both}", "animation:pop .5s var(--over) calc(var(--s6) + 3.3s) both}"),
 ("#s6 .l1{animation-delay:calc(var(--s6) + 2.3s)}#s6 .l2{animation-delay:calc(var(--s6) + 2.55s);",
  "#s6 .l1{animation-delay:calc(var(--s6) + 3.6s)}#s6 .l2{animation-delay:calc(var(--s6) + 3.85s);"),
 ("animation:pop .5s var(--over) calc(var(--s6) + 3.6s) both}", "animation:pop .5s var(--over) calc(var(--s6) + 5s) both}"),
 ("animation:pop .6s var(--over) calc(var(--s6) + 3.9s) both}", "animation:pop .6s var(--over) calc(var(--s6) + 5.4s) both}"),
 ('style="--t:var(--s6);--d:3.2s"', 'style="--t:calc(var(--s6) + .4s);--d:3.6s"'),
 ('style="--t:calc(var(--s6) + 3.3s);--d:2.7s"', 'style="--t:calc(var(--s6) + 4.9s);--d:2.7s"'),
]

bad = [(a, s.count(a)) for a, _ in R if s.count(a) != 1]
if bad:
    for a, n in bad: print(f"{n}x: {a[:90]}")
    sys.exit("substituições ambíguas ou ausentes")
for a, b in R: s = s.replace(a, b)
p.write_text(s, encoding="utf-8")
print(f"ok: {len(R)} substituições")
