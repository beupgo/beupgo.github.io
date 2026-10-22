"""Regenerate the browser bundle after editing questions.json / vocabulary.json."""
from pathlib import Path
import json
root = Path(__file__).resolve().parent
q = json.loads((root / 'questions.json').read_text(encoding='utf-8'))
v = json.loads((root / 'vocabulary.json').read_text(encoding='utf-8'))
assert len({item['id'] for item in q['questions']}) == len(q['questions'])
assert sum(item['points'] for item in q['questions']) == 100
(root / 'data.js').write_text('window.TEST_DATA = ' + json.dumps(q, ensure_ascii=False) + ';\nwindow.VOCAB_DATA = ' + json.dumps(v, ensure_ascii=False) + ';\n', encoding='utf-8')
print('Updated data.js')
