# Meridian Agro Exportação — 30s (1080×1920, 9:16)

Revisão atual: `Meridian-Agro.tsrct` ↔ `Meridian-Agro.mp4` (30,4 s, H.264 + AAC 48 kHz, 30 fps).
Gerado por `build.py` (documento editável) e `make_audio.py` (trilha + SFX procedurais).

## Mapa narração → blocos (pausas medidas por silencedetect, −38 dB)
| Bloco | Projeto | Frase |
|---|---|---|
| 1 Gancho | 0–6,25 s | "Renda previsível..." 0–3,8 / "Conheça..." 4,1–6,0 |
| 2 Tese | 6,2–14,0 s | "Uma operação..." 6,4–9,0 / "financiando..." 9,2–13,8 |
| 3 Cards | 13,95–21,3 s | "Você conta..." 14,1–17,5 / "lastro..." 17,8–21,1 |
| 4 Ticket | 21,25–26,3 s | "Aporte inicial..." 21,4–26,0 |
| 5 CTA | 26,2–30,4 s | "Acesse os documentos..." 26,3–30,2 |

## Áudio
- Narração: derivado `Sources/audio/narracao-leveled-v1.wav` (loudnorm 2 passes, receita ao lado); original preservado. Ganho 0,71 (o motor soma +3 dB ao espalhar mono em estéreo).
- Trilha: procedural (120 BPM, Am–F–C–G), swells/crash nas viradas de bloco, ganho 0,3 (~15 dB abaixo da voz).
- SFX: whoosh, clique, pop, conexão digital, contagem, trava, barra, ping — posições verificadas no mix final (±5 ms).
- Final: −15,96 LUFS integrado, −3,7 dBTP (checks/loudness-final.json). Sincronia da narração: offset 0 ms (correlação cruzada).

## Notas técnicas descobertas
- Alpha em preenchimento de Shape (sólido/gradiente) é ignorado → usar `opacity` (0–1) do fill/stroke; brilhos radiais feitos com Rect (gradiente de Rect respeita alpha).
- `trimEnd` usa 0–100. Grupos: `inputRange.start=S`, `inputOffsetMs=-S`.
- Export Linux: `--encoder-backend external-ffmpeg-command --ffmpeg-path /usr/bin/ffmpeg`.

## Pendências / limitações
- Não foi possível ouvir o resultado (verificação por medições e forma de onda).
- Trilha e SFX são sintetizados — substituíveis por trilha licenciada.
- Texto do aviso legal é um rascunho genérico: revisar com compliance.
