import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


docs = load('update_docs')
publisher = load('publish_snapshot')


class PublishingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'work'
        self.remote = Path(self.temp.name) / 'remote.git'
        subprocess.run(['git', 'init', '--bare', '--initial-branch=main', str(self.remote)], check=True, capture_output=True)
        subprocess.run(['git', 'init', '--initial-branch=main', str(self.root)], check=True, capture_output=True)
        self.git('config', 'user.name', 'beupgo')
        self.git('config', 'user.email', '2108595+beupgo@users.noreply.github.com')
        self.git('config', 'core.hooksPath', str(Path(self.temp.name) / 'no-hooks'))
        self.git('remote', 'add', 'origin', str(self.remote))
        (self.root / '.github').mkdir()
        (self.root / 'README.md').write_text('<!-- AUTO-TABLE-START -->\n<!-- AUTO-TABLE-END -->\n<!-- AUTO-FILES-START -->\n<!-- AUTO-FILES-END -->\n')
        (self.root / 'index.html').write_text('<html><body><!-- AUTO-CARDS-START -->\n<!-- AUTO-CARDS-END --></body></html>')
        (self.root / 'demo english.html').write_text('<html><head><title>英语练习</title></head><body>one</body></html>')
        (self.root / 'demo-math.html').write_text('<html><head><title>数学练习</title></head><body>two</body></html>')
        self.commit('Initial artifacts', '2020-01-01T12:00:00+08:00')
        self.git('push', 'origin', 'main')
        self.root_patch = patch.object(docs, 'ROOT', self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)

    def git(self, *args, env=None):
        return subprocess.check_output(['git', '-C', str(self.root), *args], text=True, env=env, stderr=subprocess.PIPE).strip()

    def commit(self, message, date):
        self.git('add', '--all')
        self.git('commit', '-m', message, env={**os.environ, 'GIT_AUTHOR_DATE': date, 'GIT_COMMITTER_DATE': date})
        return self.git('rev-parse', 'HEAD')

    def metadata(self):
        return json.loads((self.root / '.github/page-metadata.json').read_text())['pages']

    def test_snapshot_preserves_source_branch_and_artifacts(self):
        original = self.git('rev-parse', 'HEAD')
        self.git('push', 'origin', 'HEAD:refs/heads/source-feature')
        (self.root / 'asset.txt').write_text('latest artifact')
        docs.main()
        snapshot = publisher.publish(self.root, 'main', original)
        self.assertEqual(self.git('rev-list', '--count', snapshot), '1')
        self.assertEqual(self.git('show', snapshot + ':asset.txt'), 'latest artifact')
        self.assertEqual(self.git('write-tree'), self.git('rev-parse', snapshot + '^{tree}'))
        self.assertEqual(self.git('ls-remote', 'origin', 'refs/heads/source-feature').split()[0], original)
        self.assertEqual(self.git('show', '-s', '--format=%an <%ae>', snapshot), 'beupgo <2108595+beupgo@users.noreply.github.com>')
        self.git('reset', '--hard', snapshot)
        docs.main()
        self.assertEqual(publisher.publish(self.root, 'main', snapshot), snapshot)

    def test_concurrent_push_is_not_overwritten(self):
        original = self.git('rev-parse', 'HEAD')
        (self.root / 'new.txt').write_text('new user work')
        newer = self.commit('Concurrent change', '2021-01-01T12:00:00+08:00')
        self.git('push', 'origin', 'main')
        self.git('reset', '--hard', original)
        (self.root / 'stale.txt').write_text('stale job output')
        with self.assertRaises(subprocess.CalledProcessError):
            publisher.publish(self.root, 'main', original)
        self.assertEqual(self.git('ls-remote', 'origin', 'refs/heads/main').split()[0], newer)

    def test_wrong_checkout_is_rejected(self):
        with self.assertRaises(ValueError):
            publisher.publish(self.root, 'main', '0' * 40)
        self.assertEqual(self.git('ls-remote', 'origin', 'refs/heads/main').split()[0], self.git('rev-parse', 'HEAD'))

    def test_dates_survive_snapshots_then_only_changed_pages_update(self):
        original = self.git('rev-parse', 'HEAD')
        docs.main()
        before = self.metadata()
        self.assertIn('demo%20english.html', (self.root / 'README.md').read_text())
        snapshot = publisher.publish(self.root, 'main', original)
        self.git('reset', '--hard', snapshot)
        docs.main()
        self.assertEqual(self.metadata(), before)
        self.assertEqual(self.git('status', '--porcelain'), '')
        page = self.root / 'demo english.html'
        page.write_text(page.read_text().replace('one', 'updated lesson'))
        (self.root / 'demo-new.html').write_text('<html><title>英语新课</title><body>new</body></html>')
        changed = self.commit('Update one lesson', '2021-02-03T14:30:00+08:00')
        self.git('push', 'origin', 'main')
        docs.main()
        after = self.metadata()
        self.assertEqual(after['demo-math.html'], before['demo-math.html'])
        self.assertEqual(after['demo english.html']['uploaded_ts'], before['demo english.html']['uploaded_ts'])
        self.assertEqual(after['demo english.html']['updated_at'], '2021-02-03 14:30')
        self.assertEqual(after['demo-new.html']['uploaded_at'], '2021-02-03 14:30')
        second = publisher.publish(self.root, 'main', changed)
        self.git('reset', '--hard', second)
        docs.main()
        self.assertEqual(self.metadata(), after)
        self.assertEqual(self.git('rev-list', '--count', second), '1')
        self.assertEqual(self.git('status', '--porcelain'), '')

    def test_deleted_page_metadata_is_removed(self):
        docs.main()
        (self.root / 'demo-math.html').unlink()
        docs.main()
        self.assertNotIn('demo-math.html', self.metadata())


if __name__ == '__main__':
    unittest.main()
