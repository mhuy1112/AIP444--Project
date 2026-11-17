# Completed browser pilot - 40 observed responses

Date: 17 November 2026 (America/Toronto).

All 40 planned trials are complete. An assistant operated the websites and saved the first answer to each of ten prompts in a fresh conversation per platform. The answer key was not sent. Responses were not regenerated. These are observed product responses, not simulated outputs. Timestamps are recording times, not response durations.

## Results and scoring

The original primary rule requires a response containing only a correct number. Extra explanations fail this rule even when their final number is correct. The secondary audit, added after observing explanatory responses, compares the final nonempty numeric line with the answer key. It does not validate the explanation and does not replace the primary score.

| Platform | Completed | Strict passes | Format errors | Final number correct (secondary) |
| --- | ---: | ---: | ---: | ---: |
| ChatGPT | 10 | 10 | 0 | 10 |
| Gemini | 10 | 10 | 0 | 10 |
| Claude | 10 | 4 | 6 | 10 |
| DeepSeek | 10 | 5 | 1 | 6 |

Claude's format failures were q03, q04, q05, q06, q08 and q09; its final numbers were correct on all ten questions. DeepSeek added explanation on q03 and returned wrong final numbers on q04 (7 instead of 6), q05 (70 instead of 34), q08 (30 instead of 24), and q10 (45 instead of 27).

## Actual configurations and limitations

- ChatGPT was signed out with Default selected; its version was not disclosed. The last response showed a basic-model notice. A fixed underlying model cannot be verified.
- Gemini was signed out. The UI showed 3.5 Flash-Lite for q02-q04 and Flash-Lite elsewhere. No model switch was requested, but underlying version consistency is unverified.
- Claude was signed in on the Free plan, displaying Sonnet 5.5, Medium. Web search was switched off before testing.
- DeepSeek was signed in; its exact version was not displayed. DeepThink was off. Search was intended to be off, but the final q10 screenshot shows Search highlighted, so its state was not controlled or consistently verified across trials. The screenshot does not establish whether a web search was actually performed. This is an additional comparison confound.
- The planned four-platform rotation was not maintained because Claude and DeepSeek initially required login. Their trials ran later. Some requests overlapped across separate platform tabs. Authentication, account context and model settings differed between products.
- No response durations, tokens, API costs, or inference-time compute were measured. All time fields are blank. This run cannot support speed, cost, or inference-time scaling conclusions.
- One trial per question and ten questions per product describe this small pilot only. These results do not establish general model superiority.

## Reproducing the outputs

Run `python finalize_results.py` from this folder to validate the 40 rows, independently check the answer key, rebuild the original report and produce the secondary audit and chart. `research_manual.py --analyze` rebuilds only the original strict-scoring outputs. The original README describes the planned collection protocol; these notes document how the actual run differed.

Raw visible responses are in manual_results.csv. browser_observations.json records the later ChatGPT/Gemini observations; claude_deepseek_observations.json records the final twenty. The first two observations remain in the CSV. answer_audit.csv contains the per-question secondary review. No results were filled from the answer key.
