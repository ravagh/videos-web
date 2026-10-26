# BCG — Banner de cabeçalho 8:1 (3840×480, loop 10 s, 60 fps)

Revisão atual: `BCG-Banner.tsrct` ↔ `BCG-Banner.mp4`. Gerado por `build.py`
(`python3 -I build.py editable.json editable-vN.json` → `tsrct project commit`).

## Ideia
O logo é o centro de energia: a cada "batida" (0,15 s e 5,15 s) ele pulsa em neon azul,
dispara uma onda de choque hexagonal e o texto sai de dentro dele, caractere por caractere,
da direita (lado do logo) para a esquerda. A tag do Discord fica ancorada à direita,
com contorno pulsante e um brilho de varredura após cada entrada de texto.

## Linha do tempo (ms)
| Elemento | Tempo |
|---|---|
| "Brasil Cidade Grande" entra | 150–1050 |
| sai (sobe e desfoca, esq.→dir.) | 4300–4950 |
| "Venha jogar conosco" entra | 5150–6050 |
| sai | 9300–9950 |
| Varredura na pill do Discord | 1250–2250 / 6250–7250 |

Loop sem emenda: animações procedurais têm período que divide 10 s (2,5 s, 5 s, 10 s);
partículas sobem 48/96/144 px/s (múltiplos de 480/10).

## Estrutura
Fundo preto + brilho elíptico central, feixes angulados (ângulos da estrela), piso em
grade de perspectiva, 3 camadas de partículas, trilhos com pulsos de luz, hexágono com
luzes correndo na borda, halo neon (logo tingido + blur, modo screen), logo nítido com
outer glow, textos com Text Animator (seletor square: offset 0→−1 entrada, −1→0 saída),
tag Discord (grupo) com máscara alpha para o brilho.

## Notas técnicas
- Seletor `smooth` deixa as pontas do texto visíveis com offset 0 → usar `square`
  (dá peso fracionário por caractere, transição suave).
- Linux: render via Mesa lavapipe (`mesa-vulkan-drivers`); export com
  `--encoder-backend external-ffmpeg-command --ffmpeg-path /usr/bin/ffmpeg`.
- Fonte: Outfit (OFL, Google Fonts), instâncias estáticas 600/800 geradas com fontTools.
