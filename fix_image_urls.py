import json

with open('pins_queue.json', encoding='utf-8') as f:
    q = json.load(f)

BASE = 'https://raw.githubusercontent.com/Saiteja9989/pinterest-automation/main/'
fixed = 0

for pin in q['pins']:
    url = pin.get('image_url', '')
    if url and not url.startswith('http'):
        clean = url.replace('\\', '/')
        pin['image_url'] = BASE + clean
        fixed += 1

print(f'Fixed {fixed} image URLs')
print('Sample:', q['pins'][0]['image_url'])

with open('pins_queue.json', 'w', encoding='utf-8') as f:
    json.dump(q, f, indent=2, ensure_ascii=False)
print('Saved.')
