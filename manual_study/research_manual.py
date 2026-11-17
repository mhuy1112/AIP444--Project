"""Manual ChatGPT, Gemini, Claude, and DeepSeek pilot. No API calls or keys.
Run normally for guided entry, or --analyze to summarize the CSV.
All responses must be collected by the student. Blank rows are not results.
"""
import argparse
import csv
import html
import json
import math
import re
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from statistics import mean

BASE = Path(__file__).resolve().parent
FIELDS = ['question_id', 'platform', 'model_or_mode', 'run_date', 'answer', 'seconds', 'status', 'notes']
PLATFORMS = ('ChatGPT', 'Gemini', 'Claude', 'DeepSeek')
WEBSITES = {
    'ChatGPT': 'https://chatgpt.com/',
    'Gemini': 'https://gemini.google.com/',
    'Claude': 'https://claude.ai/',
    'DeepSeek': 'https://chat.deepseek.com/',
}
COLORS = ('#3366cc', '#19856b', '#b86627', '#8054b8')
INSTRUCTION = 'Solve the problem. Return only the final numeric answer, with no explanation or units.'


def questions():
    return json.loads((BASE / 'questions.json').read_text(encoding='utf-8'))


def template(qs):
    rows = []
    for i, q in enumerate(qs):
        offset = i % len(PLATFORMS)
        order = PLATFORMS[offset:] + PLATFORMS[:offset]
        for platform in order:
            row = dict.fromkeys(FIELDS, '')
            row.update(question_id=q['id'], platform=platform, status='pending')
            rows.append(row)
    return rows


def write_csv(path, rows, fields):
    # Atomic replacement prevents a partial table if saving is interrupted.
    temporary = path.with_suffix(path.suffix + '.tmp')
    with temporary.open('w', newline='', encoding='utf-8-sig') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def number(value):
    value = value.strip()
    if re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)', value):
        return Decimal(value)
    return None


def duration(value):
    if not value.strip():
        return None
    try:
        seconds = float(value.replace(',', '.'))
    except ValueError:
        raise ValueError('Time must be a number of seconds, or blank.') from None
    if not math.isfinite(seconds) or seconds <= 0:
        raise ValueError('Time must be finite and greater than zero.')
    return seconds


def validate(rows, qs, platforms=PLATFORMS):
    keys = {(q['id'], p) for q in qs for p in platforms}
    seen = set()
    for row in rows:
        if set(row) != set(FIELDS) or any(not isinstance(row[f], str) for f in FIELDS):
            raise ValueError('Malformed CSV row. Keep every column and quote answers containing commas.')
        key = (row['question_id'], row['platform'])
        if key not in keys or key in seen:
            raise ValueError('Unknown or duplicate question/platform row: ' + str(key))
        seen.add(key)
        if row['status'] not in ('pending', 'completed', 'error'):
            raise ValueError('Status must be pending, completed, or error: ' + str(key))
        if row['status'] == 'pending':
            if row['answer'].strip() or row['seconds'].strip():
                raise ValueError('Row has data but is still pending. Set status first: ' + str(key))
            continue
        if not row['model_or_mode'].strip() or not row['run_date'].strip():
            raise ValueError('Recorded rows need model_or_mode and run_date: ' + str(key))
        if row['status'] == 'completed' and not row['answer'].strip():
            raise ValueError('Completed row has no answer: ' + str(key))
        duration(row['seconds'])
    if seen != keys:
        raise ValueError(f'Keep all {len(keys)} template rows; leave untested rows pending.')
    for platform in platforms:
        modes = {r['model_or_mode'] for r in rows if r['platform'] == platform and r['status'] != 'pending'}
        if len(modes) > 1:
            raise ValueError('Mixed model/mode labels for ' + platform + '. Use one fixed mode per platform for this pilot.')


def load_rows(path, qs):
    if not path.exists():
        write_csv(path, template(qs), FIELDS)
    with path.open(newline='', encoding='utf-8-sig') as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != FIELDS:
            raise ValueError('CSV headers changed. Restore the original headers.')
        rows = list(reader)
    # Upgrade only a complete, valid original two-platform table.
    # Preserve every existing field; never silently repair a damaged table.
    if {r.get('platform') for r in rows} == {'ChatGPT', 'Gemini'}:
        validate(rows, qs, ('ChatGPT', 'Gemini'))
        existing = {(r['question_id'], r['platform']): r for r in rows}
        rows = [existing.get((r['question_id'], r['platform']), r) for r in template(qs)]
        validate(rows, qs)
        write_csv(path, rows, FIELDS)
        print('Added pending Claude and DeepSeek trials. Existing responses were preserved.')
    validate(rows, qs)
    return rows


def correct(row, answer_key):
    return row['status'] == 'completed' and number(row['answer']) == Decimal(answer_key[row['question_id']])


def summarize(rows, qs):
    answer_key = {q['id']: q['answer'] for q in qs}
    summaries = []
    for platform in PLATFORMS:
        group = [r for r in rows if r['platform'] == platform]
        recorded = [r for r in group if r['status'] != 'pending']
        completed = [r for r in recorded if r['status'] == 'completed']
        times = [duration(r['seconds']) for r in completed if r['seconds'].strip()]
        n_correct = sum(correct(r, answer_key) for r in recorded)
        summaries.append({'platform': platform,
            'model_or_mode': recorded[0]['model_or_mode'] if recorded else '',
            'planned': len(group), 'recorded': len(recorded), 'pending': len(group) - len(recorded),
            'completed': len(completed), 'errors': len(recorded) - len(completed),
            'correct': n_correct,
            'accuracy_recorded_pct': round(100 * n_correct / len(recorded), 2) if recorded else '',
            'numeric_format_errors': sum(number(r['answer']) is None for r in completed),
            'timed_completed': len(times), 'mean_seconds': round(mean(times), 2) if times else ''})
    # Paired columns use the common question set across all four platforms.
    lookup = {(r['question_id'], r['platform']): r for r in rows}
    paired = [q['id'] for q in qs if all(lookup[(q['id'], p)]['status'] != 'pending' for p in PLATFORMS)]
    timed = [qid for qid in paired if all(lookup[(qid, p)]['status'] == 'completed' and
              lookup[(qid, p)]['seconds'].strip() for p in PLATFORMS)]
    for item in summaries:
        platform = item['platform']
        item['paired_questions'] = len(paired)
        item['paired_accuracy_pct'] = round(100 * sum(correct(lookup[(qid, platform)], answer_key) for qid in paired) / len(paired), 2) if paired else ''
        item['paired_timed_questions'] = len(timed)
        item['paired_mean_seconds'] = round(mean(duration(lookup[(qid, platform)]['seconds']) for qid in timed), 2) if timed else ''
    return summaries


def collect(rows, qs, path):
    print('\nPlatforms: ' + ', '.join(PLATFORMS))
    print(f'{len(qs)} questions x {len(PLATFORMS)} platforms = {len(rows)} trials.')
    print('Open the indicated website yourself. Use a NEW chat for every question.')
    print('Start a stopwatch when you press Send; stop when the full answer finishes.')
    print('Do not send the answer key. Keep the same model/mode throughout.')
    print('Enter blank to skip for now. Enter /quit to exit; earlier completed entries stay saved.\n')
    print('SETUP: Enter model names only, not questions. Press Enter if unknown.')
    print('This terminal records results; it does not send questions to AI websites.\n')
    labels = {}
    for platform in PLATFORMS:
        previous = [r['model_or_mode'] for r in rows if r['platform'] == platform and r['status'] != 'pending']
        if previous:
            labels[platform] = previous[0]
            print(platform + ' saved model/mode: ' + previous[0])
        else:
            while True:
                label = input(platform + ' MODEL NAME ONLY (Enter if unknown): ').strip()
                if label == '/quit':
                    return
                lowered = label.casefold()
                if (len(label) > 120 or 'solve the problem' in lowered or
                        any(q['prompt'].casefold() in lowered for q in qs)):
                    print('That looks like a question, not a model name. It was not saved.')
                    print('Press Enter to skip this model name. Questions go in the website chat box.')
                    continue
                break
            labels[platform] = label or 'Unknown - not displayed'
    lookup = {q['id']: q for q in qs}
    for i, row in enumerate(rows, 1):
        if row['status'] != 'pending':
            continue
        q = lookup[row['question_id']]
        print('\n' + '=' * 60)
        print(f"[{i}/{len(rows)}] {row['platform']} / {q['id']}")
        print('STEP 1 - In your browser, open a NEW chat at ' + WEBSITES[row['platform']])
        print('STEP 2 - Send the prompt below in that website, not in this terminal.')
        print('STEP 3 - Return here and paste the response you received.')
        print('COPY ONLY THE PROMPT BELOW:\n')
        print(INSTRUCTION + '\n\n' + q['prompt'])
        print('\nEND OF PROMPT')
        answer = input('RESPONSE FROM WEBSITE (not the question; /quit to exit): ').strip()
        if answer == '/quit':
            return
        if not answer:
            continue
        # Keep the exact response. Non-numeric responses count as format errors.
        status = 'error' if answer == '/error' else 'completed'
        while True:
            seconds = input('Measured seconds (Enter if not measured): ').strip()
            if seconds == '/quit':
                print('Current trial was not saved. Previously completed trials are safe.')
                return
            try:
                duration(seconds)
                break
            except ValueError as exc:
                print(exc)
        note = input('Notes (Enter to leave blank): ').strip() if status == 'error' else ''
        if note == '/quit':
            print('Current trial was not saved. Previously completed trials are safe.')
            return
        row.update(answer='' if status == 'error' else answer, seconds=seconds,
                   status=status, model_or_mode=labels[row['platform']],
                   run_date=datetime.now().astimezone().isoformat(timespec='seconds'), notes=note)
        write_csv(path, rows, FIELDS)
        print('Saved.')


def make_report(rows, qs, directory):
    directory.mkdir(parents=True, exist_ok=True)
    summaries = summarize(rows, qs)
    write_csv(directory / 'summary.csv', summaries, list(summaries[0]))
    columns = ['platform', 'model_or_mode', 'recorded', 'pending', 'correct', 'errors',
               'accuracy_recorded_pct', 'timed_completed', 'mean_seconds',
               'paired_questions', 'paired_accuracy_pct', 'paired_timed_questions', 'paired_mean_seconds']
    cells = lambda values: ''.join('<td>' + html.escape(str(v)) + '</td>' for v in values)
    table = '<table><tr>' + ''.join('<th>' + c.replace('_', ' ') + '</th>' for c in columns) + '</tr>'
    table += ''.join('<tr>' + cells([r[c] for c in columns]) + '</tr>' for r in summaries) + '</table>'
    charts = ''
    for field, title, unit in [('accuracy_recorded_pct', 'Accuracy on recorded attempts', '%'),
                               ('mean_seconds', 'Mean measured response time', ' s')]:
        values = [r[field] for r in summaries if r[field] != '']
        maximum = 100 if unit == '%' else max(max(values, default=1), 0.01)
        charts += '<h2>' + title + '</h2>'
        for r in summaries:
            value = r[field]
            count = r['recorded'] if unit == '%' else r['timed_completed']
            label = 'No data' if value == '' else f'{value}{unit} (n={count})'
            width = 0 if value == '' else 100 * value / maximum
            charts += f'<p><b>{r["platform"]}</b>: {label}</p><div class="track"><div class="bar" style="width:{width}%"></div></div>'
    document = '''<!doctype html><html lang="en"><meta charset="utf-8"><title>AIP444 manual pilot</title>
<style>body{font-family:Arial,sans-serif;max-width:1100px;margin:40px auto;padding:0 24px;color:#172438}
table{border-collapse:collapse;font-size:12px}td,th{border:1px solid #ccd4df;padding:8px;text-align:left}
.scroll{overflow-x:auto}.track{background:#edf1f7;height:24px;max-width:650px}.bar{height:24px;background:#3366cc}
p{line-height:1.6}h2{margin-top:30px}</style>'''
    document += '<h1>ChatGPT, Gemini, Claude, and DeepSeek: manual pilot</h1>'
    document += '<p>Generated ' + datetime.now().astimezone().isoformat(timespec='seconds') + '</p>'
    document += '<p>Pending rows are excluded. Errors count as unsuccessful recorded attempts. Exact numeric answers only; formatting failures count as incorrect. Time averages include completed answers with a measured time, including wrong answers. Missing times are never zero.</p>'
    document += '<div class="scroll">' + table + '</div>' + charts
    document += '<h2>Interpretation</h2><p>Paired columns use only questions attempted on all four platforms; paired timing also requires a completed response and measured time on all four. Check coverage before comparing unpaired bars. This small, one-repeat pilot measures user-observed accuracy and end-to-end response time. Manual timing includes interface and network effects. It does not measure reasoning tokens, API cost, or inference-time compute. Platform names do not identify fixed models. Record the actual displayed model and mode; unknown labels limit reproducibility. Do not claim general model superiority or that slower responses prove more reasoning.</p></html>'
    (directory / 'report.html').write_text(document, encoding='utf-8')
    # Optional publication/export chart. The HTML report always works without packages.
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print('HTML charts are ready. PNG export skipped: matplotlib not installed.')
    else:
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
        for ax, field, title, ylabel in zip(axes, ['accuracy_recorded_pct', 'mean_seconds'],
                ['Accuracy (recorded attempts)', 'Mean time (measured completions)'], ['Accuracy (%)', 'Seconds']):
            for index, r in enumerate(summaries):
                value = r[field]
                if value == '':
                    ax.text(index, 0, 'No data', ha='center', va='bottom')
                else:
                    n = r['recorded'] if field == 'accuracy_recorded_pct' else r['timed_completed']
                    ax.bar(index, value, color=COLORS[index % len(COLORS)], width=.55)
                    ax.annotate(f'{value:g}\nn={n}', (index, value), xytext=(0, 4), textcoords='offset points', ha='center')
            ax.set_xticks(range(len(PLATFORMS)), PLATFORMS)
            ax.set_xlim(-.6, len(PLATFORMS) - .4)
            ax.set_ylim(0, 115 if field == 'accuracy_recorded_pct' else max([r[field] for r in summaries if r[field] != ''] + [1]) * 1.35)
            ax.set_title(title, fontsize=11)
            ax.set_ylabel(ylabel)
        fig.suptitle('Manual pilot - descriptive results only')
        fig.tight_layout()
        fig.savefig(directory / 'comparison.png', dpi=180)
        plt.close(fig)
    print('Report: ' + str(directory / 'report.html'))
    print('Summary: ' + str(directory / 'summary.csv'))
    for r in summaries:
        print(f"{r['platform']}: {r['recorded']}/{r['planned']} recorded, {r['correct']} correct, {r['pending']} pending.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--analyze', action='store_true', help='Analyze existing CSV without asking for answers.')
    args = parser.parse_args()
    path = BASE / 'manual_results.csv'
    try:
        qs = questions()
        rows = load_rows(path, qs)
        if not args.analyze:
            collect(rows, qs, path)
        validate(rows, qs)
        make_report(rows, qs, BASE / 'output')
    except KeyboardInterrupt:
        print('\nStopped. Previously saved rows are safe; rerun to continue.')
        return 0
    except (ValueError, OSError) as exc:
        print('Please fix: ' + str(exc))
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
