import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    'update_docs_subjects', Path(__file__).resolve().parents[1] / 'update_docs.py'
)
docs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(docs)


class SubjectTests(unittest.TestCase):
    def test_english_titles_and_descriptions(self):
        for title in ('BJ Primary English Collocations · 学习台', 'ENGLISH practice',
                      '小学英语练习', 'Vocabulary review', '代词专项训练'):
            with self.subTest(title=title):
                self.assertEqual(docs.infer_subject_slug(title), 'english')
        self.assertEqual(docs.infer_subject_slug('学习台', 'Primary English practice'), 'english')
        self.assertEqual(docs.infer_subject_slug('BJ Primary &#69;nglish'), 'english')

    def test_filename_separators_and_encoding(self):
        for filename in ('Primary English Collocations.html', 'primary_english.html',
                         'primary-English-practice.html', 'Primary%20English.html',
                         'English.html', 'english5.html', 'BJ.English.html',
                         'health-matters-vocabulary.html', 'nature-dialogues.html'):
            with self.subTest(filename=filename):
                self.assertEqual(docs.infer_subject_from_filename(filename), 'english')
        for filename in ('primary-advanced.html', 'earth.html', 'pearl.html',
                         'englishman.html', 'natural-health.html'):
            with self.subTest(filename=filename):
                self.assertIsNone(docs.infer_subject_from_filename(filename))

    def test_body_and_headings_fallback(self):
        for body in ('<h1>北京小学英语 · 学习台</h1>',
                     '<main><p>English vocabulary practice</p></main>',
                     '<h2>北京小学<span>英语</span>学习台</h2>',
                     '<h1>Primary &#69;nglish</h1>', '<svg/><h1>英语</h1>'):
            with self.subTest(body=body):
                text = '<html><head><title>学习台</title></head><body>' + body + '</body></html>'
                self.assertEqual(docs.extract_subject_slug(text, '学习台', 'lesson.html'), 'english')

    def test_ignore_non_learning_content(self):
        text = '''<html lang="en"><head><style>.english { color: red; }</style></head>
        <body><!-- saved from https://example.com/english -->
        <script>const title = "英语"; const history = [];</script>
        <style>.grammar { color: red; }</style><svg><title>English</title></svg>
        <nav>英语导航</nav><template>英语</template><noscript>English</noscript>
        <main>Learning station</main></body></html>'''
        self.assertIsNone(docs.extract_subject_slug(text, '学习台', 'lesson.html'))

    def test_explicit_subject_priority(self):
        self.assertEqual(docs.extract_subject_slug('<meta name="subject" content="math">',
                                                 'English', 'grade6-english.html'), 'math')
        self.assertEqual(docs.extract_subject_slug('<!-- AUTO-SUBJECT: chinese -->',
                                                 'English', 'english.html'), 'chinese')
        self.assertEqual(docs.infer_subject_slug('语文对话写作', '英语例句'), 'chinese')
        self.assertEqual(docs.extract_subject_slug('<h1>数学</h1><p>英语</p>', '练习'), 'math')

    def test_generic_topics_are_not_english(self):
        for title in ('健康知识', '奇妙的大自然', '表达观点', '句子练习', '对话练习'):
            with self.subTest(title=title):
                self.assertIsNone(docs.infer_subject_slug(title))

    def test_collect_and_both_generated_outputs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'Primary English Collocations.html').write_text(
                '<html><title>BJ Primary English Collocations · 学习台</title><body>英语</body></html>'
            )
            (root / 'lesson.html').write_text('<html><title>学习台</title><body><h1>英语</h1></body></html>')
            (root / 'grade6-english.html').write_text(
                '<html><meta name="subject" content="math"><title>数学</title><body>数学</body></html>'
            )
            with patch.object(docs, 'ROOT', root), patch.object(docs, 'get_git_uploaded_at', return_value=(0, '')), \
                    patch.object(docs, 'get_git_last_updated', return_value=(0, '')):
                pages = docs.collect_pages()
                subjects = {p['file']: p['subject_slug'] for p in pages}
                self.assertEqual(subjects['grade6-english.html'], 'math')
                self.assertEqual(subjects['lesson.html'], 'english')
                self.assertEqual(subjects['Primary English Collocations.html'], 'english')
                readme = docs.gen_readme_table(pages)
                cards = docs.gen_cards(pages)
                self.assertIn('### 英语', readme)
                self.assertNotIn('未分类', readme)
                self.assertNotIn('subject-heading">其他', cards)
                self.assertIn('Primary%20English%20Collocations.html', readme)
                self.assertIn('href="Primary English Collocations.html"', cards)

    def test_current_repository_pages_keep_their_subjects(self):
        pages = {p['file']: p['subject_slug'] for p in docs.collect_pages()}
        for filename in ('Primary English Collocations.html', 'health-matters-vocabulary.html',
                         'beijing-primary-nature-dialogues.html', 'beijing-primary-opinion-dialogues.html'):
            with self.subTest(filename=filename):
                self.assertEqual(pages[filename], 'english')
        self.assertTrue(all(pages.values()), 'Existing learning pages must remain classified')


if __name__ == '__main__':
    unittest.main()
