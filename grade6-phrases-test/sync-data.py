from pathlib import Path
import json
root=Path(__file__).resolve().parent
d=json.loads((root/'questions.json').read_text());v=json.loads((root/'vocabulary.json').read_text())
assert len({q['id'] for q in d['questions']})==60
assert sum(q['points'] for q in d['questions'])==120
(root/'data.js').write_text('window.TEST_DATA = '+json.dumps(d,ensure_ascii=False)+';\nwindow.VOCAB_DATA = '+json.dumps(v,ensure_ascii=False)+';\n')
