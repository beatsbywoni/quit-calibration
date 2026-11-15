# Termination inference vs Lichess API status

requested 4101, returned 4101

| inferred | api status | n | consistent |
|---|---|---|---|
| draw | draw | 639 | yes |
| draw | insufficientMaterialClaim | 6 | NO |
| draw | outoftime | 164 | yes |
| draw | stalemate | 175 | yes |
| draw | timeout | 16 | yes |
| mate | mate | 1000 | yes |
| other | aborted | 1 | yes |
| other | cheat | 3 | yes |
| other | noStart | 97 | yes |
| resign | resign | 1000 | yes |
| time | outoftime | 956 | yes |
| time | timeout | 44 | yes |

precision of inferred "resign": 1000/1000 = 1.0000

precision of inferred "mate": 1000/1000 = 1.0000

precision of inferred "time": 1000/1000 = 1.0000
