# AIP444: ChatGPT, Gemini, Claude, and DeepSeek Study

Compare accuracy and response time on ten numeric reasoning questions. You collect the responses in the websites; Python saves and analyzes the results. No API key is required.

| Platform | Website | What to record |
| --- | --- | --- |
| ChatGPT | https://chatgpt.com/ | The model and mode displayed in your account. |
| Gemini | https://gemini.google.com/ | The model and mode displayed in your account. |
| Claude | https://claude.ai/ | The model and mode displayed in your account. |
| DeepSeek | https://chat.deepseek.com/ | The model and thinking mode displayed in your account. |

These are platform names, not four specific model versions. Use the same model and mode within each platform. If the underlying model is not displayed, record it as unknown rather than guessing. The platform names alone are not valid model identifiers.

## Start

1. Double-click `start_manual.cmd`.
2. Enter the model or mode displayed in each website. Press Enter if it is not displayed; do not guess.
3. The program tells you which platform to use and shows the prompt to copy.
4. Open a **new chat** on that platform. Copy only the text between `COPY ONLY THE PROMPT BELOW` and `END OF PROMPT`.
5. Start a stopwatch when you press Send. Stop it when the complete response finishes appearing.
6. Paste the exact one-line response into the terminal. Enter the measured seconds, such as `4.6`. Leave time blank if you did not measure it.
7. Repeat for all 40 trials: ten questions on each of the four platforms.

The program upgrades the original 20-row ChatGPT/Gemini CSV to 40 rows automatically. It preserves all existing fields and adds pending Claude/DeepSeek trials. A malformed or incomplete table is rejected instead of overwritten.

Each completed entry is saved immediately. Enter `/quit` at the answer prompt to stop, then reopen the program to continue. Press Enter at the answer prompt to skip a question temporarily. Enter `/error` if you attempted a question but the website failed to return an answer, and record the reason.

## Files

| File | Purpose |
| --- | --- |
| `start_manual.cmd` | Starts the program on Windows. |
| `research_manual.py` | Collects answers, checks results, and produces reports. |
| `questions.json` | Questions and the local answer key. Do not send this file to any model. |
| `manual_results.csv` | Your recorded responses and timings. Pending rows have no results yet. |
| `README.md` | These instructions. |

The program creates an `output` folder with `summary.csv` and `report.html`. Open the HTML file in a browser to see the table and charts. If matplotlib is installed, it also exports `comparison.png` for your report; otherwise, the HTML charts still work.

To analyze an edited CSV without entering more answers, run this command from the `manual_study` folder:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python314\python.exe" research_manual.py --analyze
```

If Python is installed elsewhere, use your installed Python executable instead.

## Keep the comparison consistent

- Use identical prompts and a new conversation for every trial. Do not use a conversation that already contains the answer key.
- Keep the same model and mode for each platform throughout the study. Turn off web search and other optional tools for these self-contained questions. Record relevant differences in tools, memory, or custom instructions in the `notes` column. If a service changes the model or mode, pause rather than mixing different configurations under one label.
- Follow the displayed order. The four-platform order rotates between questions; with ten questions, positions are approximately balanced.
- Record the first response. Do not regenerate until you obtain a correct answer.
- Do not change questions after seeing the results. To repeat the entire study, use a separate copy with an empty results table.
- Leave unmeasured times blank. Do not invent results, timings, token counts, or costs.

For a multiline response, paste the full response into the CSV's `answer` cell using a spreadsheet editor. Set `status` to `completed`, enter the model/mode and date, and include measured seconds if available. Save as UTF-8 CSV and close the spreadsheet before running Python. Keep the headers and all 40 rows. The prompt requests only a number, so extra explanations count as format errors under this scoring rule.

## Understand the results

| Column | Meaning |
| --- | --- |
| `recorded` | Attempted trials, including completed responses and service errors. |
| `pending` | Unattempted trials; excluded from accuracy calculations. |
| `correct` | Numeric responses matching the answer key; `66` and `66.0` are equivalent. |
| `accuracy_recorded_pct` | Correct responses divided by recorded attempts, multiplied by 100. Service and format errors count as unsuccessful attempts. |
| `timed_completed` | Completed responses with a measured time. |
| `mean_seconds` | Mean time for measured completed responses, including wrong answers. Missing times are not zero. |
| `paired_questions` | Questions attempted on all four platforms. |
| `paired_accuracy_pct` | Accuracy on that common set of questions. |
| `paired_timed_questions` | Questions with completed responses and measured times on all four platforms. |
| `paired_mean_seconds` | Mean time on that common timed set. |

Use paired columns when coverage differs. Completing all 40 trials makes the comparison easier to interpret. Until at least one question is attempted on all four platforms, paired accuracy is blank, not zero.

## Scope and limitations

This is a small product-comparison pilot using ten original questions and one trial per question per platform. It measures observed accuracy and end-to-end response time. Manual timing includes network, interface, and human timing effects. Product names do not identify fixed underlying models; unknown model labels limit reproducibility.

The study does not isolate inference-time scaling or measure reasoning tokens or API cost. A slower response does not prove that a model used more reasoning. If the assignment requires a controlled scaling experiment, supplement this pilot with a suitable within-model comparison. Do not claim general model superiority from these ten questions.

## Methodology paragraph

Use the following only after actually following the procedure:

> We conducted a small manual pilot using ten numeric reasoning problems on ChatGPT, Gemini, Claude, and DeepSeek, giving 40 planned trials. Each problem was submitted once per platform in a new conversation using identical wording. Platform order rotated across questions. We recorded the displayed model and mode, the first response, and manually measured time from submission to completion. A Python script checked numeric answers and summarized accuracy and response time. Unattempted trials and missing timing values were kept separate. Common-question comparisons included only questions attempted on all four platforms. This comparison describes user-observed product performance; it does not isolate inference-time scaling or measure reasoning tokens or API cost.

Write the results and conclusions only after collecting real responses.
