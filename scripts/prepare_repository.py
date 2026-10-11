"""Set public repository metadata before pushing. Never accepts a token."""
import argparse
import json
from pathlib import Path
import re
parser = argparse.ArgumentParser()
parser.add_argument('owner', help='GitHub user or organization')
parser.add_argument('--repository', default='calmean-ha')
parser.add_argument('--maintainer', help='GitHub user (needed for organization repositories)')
args = parser.parse_args()
for value in (args.owner, args.repository, args.maintainer or args.owner):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', value):
        parser.error('Invalid GitHub name')
path = Path(__file__).resolve().parents[1] / 'custom_components/calmean/manifest.json'
data = json.loads(path.read_text())
data['documentation'] = f'https://github.com/{args.owner}/{args.repository}'
data['issue_tracker'] = data['documentation'] + '/issues'
data['codeowners'] = ['@' + (args.maintainer or args.owner)]
path.write_text(json.dumps(data, indent=2) + '\n')
print('Public repository metadata updated.')
