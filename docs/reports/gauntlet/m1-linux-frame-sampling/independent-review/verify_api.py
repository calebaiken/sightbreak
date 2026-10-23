"""Refetch pinned public API/source evidence, with no engine execution."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE.parent / 'API_EVIDENCE.json'


def verify(item):
    with urlopen(item['url'], timeout=30) as response:
        data = response.read(1_000_001)
    if len(data) > 1_000_000:
        raise ValueError('Independent fetch exceeded bound')
    commit_url = item['url'].replace('/4.7.2-stable/', '/ed1daf0bf/')
    with urlopen(commit_url, timeout=30) as response:
        commit_data = response.read(1_000_001)
    excerpts = [value if isinstance(value, str) else value['text'] for value in item['excerpts']]
    text = data.decode()
    result = dict(path=item['path'], url=item['url'], commit_url=commit_url,
                  bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                  committed_source_bytes_equal=data == commit_data,
                  excerpt_checks=[excerpt in text for excerpt in excerpts])
    result['passed'] = (result['bytes'] == item['bytes'] and result['sha256'] == item['sha256']
                        and result['committed_source_bytes_equal'] and all(result['excerpt_checks']))
    return result


def main():
    document = json.loads(EVIDENCE.read_text())
    assert document['release'] == '4.7.2-stable'
    assert document['engine_commit'] == 'ed1daf0bf'
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(verify, document['sources']))
    output = dict(scope='Independent public HTTP fetch; no engine or native execution',
                  evidence_sha256=hashlib.sha256(EVIDENCE.read_bytes()).hexdigest(), results=results,
                  passed=all(item['passed'] for item in results))
    print(json.dumps(output, indent=2))
    assert output['passed']


if __name__ == '__main__':
    main()
