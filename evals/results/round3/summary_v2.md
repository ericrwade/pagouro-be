# Gate summary — judge google/gemini-2.5-flash, 2026-09-29

| arm | group | n | subject | style | legible text | unasked lettering |
|---|---|---|---|---|---|---|
| ft | ALL | 160 | 131/160 (82 %) | 147/160 (92 %) | 2/24 | 136/160 (85 %) |
| ft | people | 32 | 30/32 (94 %) | 28/32 (88 %) | — | 23/32 (72 %) |
| ft | animals | 24 | 22/24 (92 %) | 20/24 (83 %) | — | 18/24 (75 %) |
| ft | objects | 24 | 24/24 (100 %) | 24/24 (100 %) | — | 23/24 (96 %) |
| ft | places | 24 | 23/24 (96 %) | 24/24 (100 %) | — | 20/24 (83 %) |
| ft | lettering | 24 | 2/24 (8 %) | 24/24 (100 %) | 2/24 | 24/24 (100 %) |
| ft | impossible | 32 | 30/32 (94 %) | 27/32 (84 %) | — | 28/32 (88 %) |
| ft_neg | ALL | 160 | 127/160 (79 %) | 145/160 (91 %) | 2/24 | 136/160 (85 %) |
| ft_neg | people | 32 | 31/32 (97 %) | 28/32 (88 %) | — | 28/32 (88 %) |
| ft_neg | animals | 24 | 21/24 (88 %) | 20/24 (83 %) | — | 15/24 (62 %) |
| ft_neg | objects | 24 | 24/24 (100 %) | 23/24 (96 %) | — | 20/24 (83 %) |
| ft_neg | places | 24 | 23/24 (96 %) | 24/24 (100 %) | — | 20/24 (83 %) |
| ft_neg | lettering | 24 | 2/24 (8 %) | 24/24 (100 %) | 2/24 | 24/24 (100 %) |
| ft_neg | impossible | 32 | 26/32 (81 %) | 26/32 (81 %) | — | 29/32 (91 %) |

## Human sample (Eric, 2026-09-29, 40 pictures from the round-3 candidate, one seed per caption)

| arm | n | human: subject | human: style | human: words legible |
|---|---|---|---|---|
| ft (round 3) | 40 | 34/40 (85 %) | 36/40 (90 %) | 0/6 |

Judge (gemini-2.5-flash, rubric v2) agrees with the human on subject 34/40 (85 %), style 36/40 (90 %),
words 6/6. Disagreements now go both ways: four human-yes / judge-no, all on lettering captions where the
strict judge requires the asked word itself and the person accepted the picture (a cafe doorway with a
sign, a bicycle-race poster with 'VEEO LO'); two judge-yes / human-no (a rocket, the singer's raised hand).
Code and per-picture rows: `human_sample/human_scores.json`.
