# Company brain: with and without Knowledge Indicators

Same questions, same data, same model. One agent reads Knowledge Indicators from the AI Index first; the baseline explores the indices by itself. "Correct" means the answer names exactly the records computed from the data files. Runs from 2026-11-18. Where a question has no baseline row, the baseline was not run for it, to save tokens.

| Question | Agent | Correct | Tool calls | LLM calls | Tokens | Seconds |
|---|---|---|---|---|---|---|
| location (en) | Baseline, no context | yes | 10 | 27 | 348,407 | 77 |
| location (en) | With Knowledge Indicators | yes | 3 | 4 | 48,474 | 21 |
| overdue (de) | Baseline, no context | yes | 2 | 7 | 56,617 | 34 |
| overdue (de) | With Knowledge Indicators | yes | 2 | 3 | 31,558 | 20 |
| late-breaches (fr) | Baseline, no context | yes | 6 | 14 | 123,958 | 43 |
| late-breaches (fr) | With Knowledge Indicators | yes | 8 | 8 | 99,134 | 35 |

## Per agent (averages per question)

| Agent | Correct | Tool calls | Tokens | Seconds |
|---|---|---|---|---|
| Baseline, no context | 3 of 3 | 6.0 | 176,327 | 51 |
| With Knowledge Indicators | 3 of 3 | 4.3 | 59,722 | 25 |

## The questions

- **location**: Which outsourcing arrangements store client data outside Switzerland, and does our directive allow each of them?  
  Expected: OUT-003, OUT-004, OUT-014, OUT-019. Not allowed: OUT-003, OUT-014, OUT-019. Allowed (EU with board approval): OUT-004.
- **overdue**: Bei welchen aktiven Auslagerungen ist die jährliche Überprüfung überfällig?  
  Expected: OUT-002, OUT-007, OUT-010. Overdue means last review more than 12 months ago (W-12 v3.0, section 8).
- **late-breaches**: Quelles violations de la sécurité des données ont été annoncées en retard cette année, et lesquelles concernent un prestataire externe ?  
  Expected: INC-2026-023, INC-2026-043. Late means not reported within 24 hours (P-11). With a provider: INC-2026-043 (OUT-019).

Agents are not deterministic. One run per question shows direction, not proof. The full answers are in `brain/answers/`.
