import json

with open('pins_queue.json', encoding='utf-8') as f:
    q = json.load(f)

FIXES = {
    '\u00e2\u20ac\u201d': '\u2014',  # em dash —
    '\u00e2\u20ac\u2122': '\u2019',  # right single quote '
    '\u00e2\u20ac\u0153': '\u201c',  # left double quote "
    '\u00e2\u20ac\u009d': '\u201d',  # right double quote "
    '\u00e2\u2020\u2019': '\u2192',  # arrow →
}

fixed_count = 0
for pin in q['pins']:
    for key in ('title', 'description'):
        val = pin.get(key, '')
        new_val = val
        for bad, good in FIXES.items():
            new_val = new_val.replace(bad, good)
        if new_val != val:
            pin[key] = new_val
            fixed_count += 1

with open('pins_queue.json', 'w', encoding='utf-8') as f:
    json.dump(q, f, indent=2, ensure_ascii=False)

print(f'Fixed {fixed_count} fields. Saved.')
