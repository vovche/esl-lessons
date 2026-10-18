"""Guard the reviewed SEL integration and keep it separate from language scores."""
import json
import re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'teacher/sel-official-source-manifest.json').read_text())
assert manifest['publisher_page']=='https://selkernels.gse.harvard.edu/uk-UA/downloads'
assert [len(b['files']) for b in manifest['bundles']]==[20,60,8]
for bundle in manifest['bundles']:
    assert bundle['url'].startswith('https://easel-kernels.s3.us-east-2.amazonaws.com/summary-files/')
    assert re.fullmatch('[0-9a-f]{64}',bundle['archive_sha256'])
    for item in bundle['files']:
        assert re.fullmatch('[0-9a-f]{64}',item['sha256']) and item['pages']>0
for grade,total in ((6,123),(7,140),(9,121)):
    folder=ROOT/'teacher'/str(grade)
    report=folder/'SEL_NUSH_REVIEW.md'
    assert report.is_file(),report
    text=report.read_text()
    assert 'https://' in text and 'Harvard' in text and '1093' in text,report
    data=json.loads((ROOT/str(grade)/'simulations.json').read_text())
    assert len(data['lessons'])==total
    for lesson in data['lessons']:
        for game in lesson['games']:
            reflection=game['reflection']
            assert set(reflection)=={'focus','prompt'},(grade,lesson['id'])
            assert all(isinstance(v,str) and v.strip() for v in reflection.values())
            assert not any(token in json.dumps(reflection,ensure_ascii=False) for token in ('teacher/','source_sha256','key.md','http://','https://'))
        for path in (folder/f"{lesson['number']:03d}").glob('*.md'):
            for target in re.findall(r'\]\(([^)]+SEL_NUSH_REVIEW\.md)\)',path.read_text()):
                assert (path.parent/target).resolve().is_file(),(path,target)
    print(f'PASS SEL/NUSH grade {grade}: {total} lessons, unscored learner reflection and source-linked review')
