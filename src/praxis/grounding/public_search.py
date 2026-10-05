"""Bounded public search adapters. Only the explicitly supplied query leaves PRAXIS."""
from datetime import datetime, timezone
from hashlib import sha256
from html import unescape
import json
import os
import re
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen


def public_search(query, provider, limit):
    if provider == 'brave':
        key = os.environ.get('PRAXIS_BRAVE_API_KEY')
        if not key:
            return {'status': 'unconfigured', 'provider': provider, 'hits': [],
                    'message': 'Set PRAXIS_BRAVE_API_KEY on the server for general web search.'}
        url = 'https://api.search.brave.com/res/v1/web/search?' + urlencode({'q': query, 'count': limit})
        headers = {'X-Subscription-Token': key}
    else:
        url = 'https://en.wikipedia.org/w/api.php?' + urlencode({
            'action': 'query', 'list': 'search', 'srsearch': query, 'srlimit': limit, 'format': 'json'})
        headers = {}
    headers.update({'User-Agent': 'PRAXIS-OS/0.9 (human-directed research; localhost)', 'Accept': 'application/json'})
    try:
        with urlopen(Request(url, headers=headers), timeout=12) as response:
            raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError('Response too large')
        data = json.loads(raw)
        if 'error' in data:
            raise ValueError('Provider error')
        rows = data.get('web', {}).get('results', []) if provider == 'brave' else data['query']['search']
        hits = []
        seen = set()
        for row in rows[:limit]:
            uri = row.get('url', '') if provider == 'brave' else 'https://en.wikipedia.org/?curid=' + str(int(row['pageid']))
            parsed = urlsplit(uri)
            if parsed.scheme not in {'https', 'http'} or not parsed.hostname or parsed.username or uri in seen:
                continue
            seen.add(uri)
            snippet = row.get('description', '') if provider == 'brave' else row.get('snippet', '')
            snippet = unescape(re.sub('<[^>]+>', '', snippet))[:1200]
            hits.append({'citation_id': 'web:' + sha256((uri+snippet).encode()).hexdigest()[:24],
                         'title': unescape(re.sub('<[^>]+>', '', row['title']))[:400], 'url': uri,
                         'excerpt': snippet, 'provider': provider,
                         'retrieved_at': datetime.now(timezone.utc).isoformat(),
                         'status': 'search_snippet_not_verified_evidence'})
        return {'status': 'ok', 'provider': provider, 'hits': hits,
                'message': 'Wikipedia encyclopedia search only.' if provider == 'wikipedia' else 'General web search snippets.'}
    except Exception:
        # Never expose headers, credentials, provider bodies, or queries in an error.
        return {'status': 'unavailable', 'provider': provider, 'hits': [],
                'message': 'Public search could not complete. Check connectivity or provider configuration; local results remain available.'}
