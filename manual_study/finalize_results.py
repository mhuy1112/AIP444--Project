"""Rebuild the completed browser pilot and its explicitly secondary audit."""
import html
import json
from decimal import Decimal
from fractions import Fraction
from itertools import permutations, product
from math import comb
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import research_manual as study

BASE = Path(__file__).resolve().parent
OUT = BASE / 'output'
qs = study.questions()
rows = study.load_rows(BASE / 'manual_results.csv', qs)
observations = json.loads((OUT / 'claude_deepseek_observations.json').read_text(encoding='utf-8'))
assert len(observations) == len({(o['question_id'], o['platform']) for o in observations}) == 20
labels = {'Claude': 'Sonnet 5.5 - Medium; signed in',
          'DeepSeek': 'Unknown version - DeepThink off; Search state not controlled; signed in'}
for observation in observations:
    row = next(r for r in rows if (r['question_id'], r['platform']) ==
               (observation['question_id'], observation['platform']))
    if row['status'] == 'completed':
        assert row['answer'] == observation['answer'], 'Existing response differs; do not overwrite.'
    else:
        assert row['status'] == 'pending'
    row.update(model_or_mode=labels[row['platform']], run_date=observation['recorded_at'],
               answer=observation['answer'], seconds='', status='completed',
               notes='First response observed through browser UI by assistant in a fresh signed-in chat. '
               'No regeneration. Captured visible answer text, including explanations. '
               'Time not measured. Collected after ChatGPT/Gemini because login was initially unavailable. '
               + ('DeepThink off; underlying version not displayed. Search state was not consistently verified; '
                  'the final q10 screenshot shows Search highlighted.' if row['platform'] == 'DeepSeek'
                  else 'Displayed model Sonnet 5.5; effort Medium; web search off.'))
study.validate(rows, qs)
assert len(rows) == 40 and all(r['status'] == 'completed' for r in rows)
assert all(not r['seconds'] for r in rows)
assert all('\ufffd' not in r['answer'] for r in rows), 'Unexpected replacement character in response.'

# Independently verify every supplied answer-key entry.
coins = [0] + [99] * 6
for value in range(1, 7):
    coins[value] = min(coins[value-c] + 1 for c in (1, 3, 4) if c <= value)
verified = [Fraction(80) * Fraction(3, 4) * Fraction(11, 10), Fraction(110-100, 2),
            sum(n for n in range(1, 101) if n % 3 and n % 5), pow(7, 103, 13),
            comb(8, 4) - comb(4, 2)**2,
            sum('11' not in ''.join(p) for p in product('01', repeat=8)), coins[6],
            sum(p.index('A') < p.index('B') and abs(p.index('C')-p.index('D')) == 1
                for p in permutations('ABCDE')),
            next(n for n in range(1, 106) if n % 3 == 2 and n % 5 == 3 and n % 7 == 2),
            sum(sum(p) == 10 for p in product(range(1, 7), repeat=3))]
assert all(Decimal(str(q['answer'])) == Decimal(int(v)) for q, v in zip(qs, verified))
study.write_csv(BASE / 'manual_results.csv', rows, study.FIELDS)
study.make_report(rows, qs, OUT)

# Secondary, post-hoc audit: it does not replace the original strict scoring rule.
key = {q['id']: q['answer'] for q in qs}
audit = []
for row in rows:
    last = row['answer'].strip().splitlines()[-1].strip()
    numeric = study.number(last)
    assert numeric is not None, 'Final answer needs manual review.'
    audit.append({'question_id': row['question_id'], 'platform': row['platform'],
                  'expected': key[row['question_id']], 'observed_final_line': last,
                  'final_numeric_correct': numeric == Decimal(key[row['question_id']]),
                  'numeric_only_format': study.number(row['answer']) is not None,
                  'primary_pass': study.correct(row, key)})
study.write_csv(OUT / 'answer_audit.csv', audit, list(audit[0]))
totals = []
for platform in study.PLATFORMS:
    group = [a for a in audit if a['platform'] == platform]
    totals.append({'platform': platform, 'completed': len(group),
                   'primary_pass': sum(a['primary_pass'] for a in group),
                   'format_errors': sum(not a['numeric_only_format'] for a in group),
                   'final_numeric_correct_posthoc': sum(a['final_numeric_correct'] for a in group)})
study.write_csv(OUT / 'accuracy_audit_summary.csv', totals, list(totals[0]))
table = '| Platform | Completed | Strict passes | Format errors | Final number correct (secondary) |\n'
table += '| --- | ---: | ---: | ---: | ---: |\n'
table += ''.join('| {platform} | {completed} | {primary_pass} | {format_errors} | {final_numeric_correct_posthoc} |\n'.format(**t) for t in totals)
notes = '''# Completed browser pilot - 40 observed responses

Date: 17 November 2026 (America/Toronto).

All 40 planned trials are complete. An assistant operated the websites and saved the first answer to each of ten prompts in a fresh conversation per platform. The answer key was not sent. Responses were not regenerated. These are observed product responses, not simulated outputs. Timestamps are recording times, not response durations.

## Results and scoring

The original primary rule requires a response containing only a correct number. Extra explanations fail this rule even when their final number is correct. The secondary audit, added after observing explanatory responses, compares the final nonempty numeric line with the answer key. It does not validate the explanation and does not replace the primary score.

''' + table + '''
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
'''
(OUT / 'RUN_NOTES.md').write_text(notes, encoding='utf-8')
report = OUT / 'report.html'
document = report.read_text(encoding='utf-8')
extra = '<h2>Completed run: 40/40</h2><p>Assistant-operated browser collection. All durations are unmeasured. Exact model consistency and the planned platform rotation were not controlled. DeepSeek Search state was not consistently verified; the final screenshot shows Search highlighted. See RUN_NOTES.md.</p>'
extra += '<h2>Secondary audit: final number only</h2><p>Post-hoc review of each final numeric line. This ignores extra explanation and does not replace the original strict scores above.</p><table><tr><th>Platform</th><th>Strict passes / 10</th><th>Format errors</th><th>Final number correct / 10</th></tr>'
extra += ''.join('<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>'.format(html.escape(t['platform']), t['primary_pass'], t['format_errors'], t['final_numeric_correct_posthoc']) for t in totals) + '</table>'
document = document.replace('<h2>Interpretation</h2>', extra + '<h2>Interpretation</h2>')
report.write_text(document, encoding='utf-8')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(9, 5))
x = list(range(4))
bars1 = ax.bar([v-.2 for v in x], [t['primary_pass'] for t in totals], .4, label='Primary: correct number only', color='#265cab')
bars2 = ax.bar([v+.2 for v in x], [t['final_numeric_correct_posthoc'] for t in totals], .4, label='Secondary: final number correct', color='#21a080')
ax.bar_label(bars1); ax.bar_label(bars2)
ax.set_xticks(x, study.PLATFORMS); ax.set_ylim(0, 12); ax.set_yticks(range(0, 11, 2))
ax.set_ylabel('Questions out of 10'); ax.set_title('Observed browser pilot: 40 completed trials')
ax.legend(loc='upper center', ncol=2, fontsize=9)
fig.text(.5, .02, 'One trial per question. Model/account settings differ. No timing measurements.', ha='center', fontsize=9)
fig.tight_layout(rect=[0,.05,1,1]); fig.savefig(OUT / 'accuracy_comparison.png', dpi=180); plt.close(fig)

archive = BASE.parents[1] / 'AIP444_Test_Results.zip'
names = ['research_manual.py', 'finalize_results.py', 'questions.json', 'manual_results.csv', 'README.md', 'start_manual.cmd',
         'output/summary.csv', 'output/report.html', 'output/comparison.png', 'output/accuracy_comparison.png',
         'output/browser_observations.json', 'output/claude_deepseek_observations.json', 'output/RUN_NOTES.md',
         'output/answer_audit.csv', 'output/accuracy_audit_summary.csv']
with ZipFile(archive, 'w', ZIP_DEFLATED) as bundle:
    for name in names:
        bundle.write(BASE / name, 'manual_study/' + name)
with ZipFile(archive) as bundle:
    assert bundle.testzip() is None and len(bundle.namelist()) == len(names)
print(json.dumps(totals, indent=2))
print('Verified 40 unique completed rows, all 10 key answers and archive integrity.')
print('Bundle:', archive)
