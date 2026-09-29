# Gate summary — judge google/gemini-2.5-flash, 2026-09-29

| arm | group | n | subject | style | legible text |
|---|---|---|---|---|---|
| base | ALL | 160 | 125/160 (78 %) | 151/160 (94 %) | 0/24 |
| base | people | 32 | 27/32 (84 %) | 32/32 (100 %) | — |
| base | animals | 24 | 18/24 (75 %) | 24/24 (100 %) | — |
| base | objects | 24 | 17/24 (71 %) | 21/24 (88 %) | — |
| base | places | 24 | 22/24 (92 %) | 22/24 (92 %) | — |
| base | lettering | 24 | 18/24 (75 %) | 23/24 (96 %) | 0/24 |
| base | impossible | 32 | 23/32 (72 %) | 29/32 (91 %) | — |
| ft | ALL | 160 | 143/160 (89 %) | 155/160 (97 %) | 0/24 |
| ft | people | 32 | 29/32 (91 %) | 31/32 (97 %) | — |
| ft | animals | 24 | 18/24 (75 %) | 23/24 (96 %) | — |
| ft | objects | 24 | 23/24 (96 %) | 24/24 (100 %) | — |
| ft | places | 24 | 23/24 (96 %) | 24/24 (100 %) | — |
| ft | lettering | 24 | 22/24 (92 %) | 22/24 (92 %) | 0/24 |
| ft | impossible | 32 | 28/32 (88 %) | 31/32 (97 %) | — |
| lora | ALL | 160 | 141/160 (88 %) | 159/160 (99 %) | 1/24 |
| lora | people | 32 | 29/32 (91 %) | 31/32 (97 %) | — |
| lora | animals | 24 | 21/24 (88 %) | 24/24 (100 %) | — |
| lora | objects | 24 | 23/24 (96 %) | 24/24 (100 %) | — |
| lora | places | 24 | 24/24 (100 %) | 24/24 (100 %) | — |
| lora | lettering | 24 | 19/24 (79 %) | 24/24 (100 %) | 1/24 |
| lora | impossible | 32 | 25/32 (78 %) | 32/32 (100 %) | — |

## Human sample (Eric, 2026-09-29, 40 blind images: 16 ft / 12 lora / 12 base, one seed per caption)

| arm | n | human: subject | human: style | human: words legible |
|---|---|---|---|---|
| base | 12 | 9/12 (75 %) | 12/12 (100 %) | 0/1 |
| ft | 16 | 11/16 (69 %) | 16/16 (100 %) | 0/2 |
| lora | 12 | 8/12 (67 %) | 12/12 (100 %) | 0/3 |

Judge (gemini-2.5-flash) agrees with the human on subject 33/40 (82 %), style 38/40 (95 %), words 6/6.
Six of the seven subject disagreements are judge=yes / human=no, four of them on lettering captions
where the judge counted "a poster with lettering" as the subject although the word was wrong. The
judge is the lenient one; the human number is the one to print. Style is saturated for every arm,
including the untuned base (the prompt prefix alone makes posters), so it does not separate arms.
Scorer's note: "there were many that had words that were jumbled and you didn't ask me about that" —
unasked lettering appears in most pictures; round 2 measures it (a fourth rubric item) and tests a
lettering negative prompt for captions that ask for no words. Code: `human_sample/human_scores.json`.
