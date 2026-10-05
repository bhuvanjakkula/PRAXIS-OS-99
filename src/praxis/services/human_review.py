"""Revision-bound advisory snapshots and append-only human review projections."""


def advice_items(revision, records):
    items = [{"id": f"revision:{revision.version}", "kind": "inquiry",
              "title": "System inquiry and proposed next steps",
              "statements": list(revision.proposed_actions),
              "limitations": "Deterministic inquiry prompts; no connected AI or independently verified recommendation."}]
    for record in records:
        if record['version'] == revision.version and record['kind'] == 'option_comparison':
            items.append({"id": record['id'], "kind": "option_comparison",
                          "title": "Saved option comparison",
                          "statements": ["Highest supplied score: " + ', '.join(record['analysis']['leaders'])],
                          "inputs": record['inputs'], "analysis": record['analysis'],
                          "limitations": record['analysis']['limitations']})
    for record in records:
        if record['version'] == revision.version and record['kind'] == 'research_memo':
            items.append({'id': record['id'], 'kind': 'research_memo', 'title': 'Search and decision memo',
                          'statements': record['analysis']['next_steps'],
                          'inputs': record['inputs'], 'analysis': record['analysis'],
                          'limitations': record['analysis']['limitations']})
    for record in records:
        if record['version'] == revision.version and record['kind'] == 'foresight_run':
            items.append({'id': record['id'], 'kind': 'foresight_run', 'title': 'Foresight and candidate solutions',
                          'statements': record['analysis']['next_steps'], 'inputs': record['inputs'],
                          'analysis': record['analysis'], 'limitations': record['analysis']['limitations']})
    for item in items:
        if item['kind'] == 'foresight_run':
            item['behavior_notes'] = ['Forecasts extrapolate supplied equally spaced observations.',
                                     'Historical backtests cannot establish reliability after a change in conditions.',
                                     'Scenario rankings depend on supplied payoffs and constraint assessments.',
                                     'Candidate solutions are untested hypotheses; review and experiment before relying on them.']
            continue
        if item['kind'] == 'research_memo':
            item['behavior_notes'] = ['Retrieves sources and structures domain questions; snippets are unverified.',
                                     'Ranks only supplied forecasts; unknown or failed constraints exclude an option.',
                                     'Missing scenarios or incorrect probabilities can change any numerical conclusion.']
            continue
        item['behavior_notes'] = (
            ["Ranks the supplied options using supplied criterion weights and scores.",
             "Missing options, unsuitable criteria or inaccurate scores can change the conclusion.",
             "Weight sensitivity is a limited numerical check, not proof of real-world reliability.",
             "Example: an option can score highest yet be unsuitable if an important constraint was omitted."]
            if item['kind'] == 'option_comparison' else
            ["Generates deterministic inquiry prompts from the current decision revision.",
             "Does not fetch external evidence or establish that proposed steps will succeed.",
             "Missing context and incorrect inputs can produce incomplete or unsuitable prompts.",
             "Example: a suggested trial may be inappropriate when a supplied constraint forbids it."])
    return items


def human_control(revision, records):
    judgments = [r for r in records if r['kind'] == 'judgment']
    current = [r for r in judgments if r['version'] == revision.version]
    items = advice_items(revision, records)
    for item in items:
        reviews = [r for r in current if r.get('advice_id') == item['id']]
        item['latest_review'] = reviews[-1] if reviews else None
        item['review_count'] = len(reviews)
        item['status'] = reviews[-1]['disposition'] if reviews else 'awaiting_human_review'
    general = [r for r in current if not r.get('advice_id')]
    return {"authority": "human", "execution_enabled": False,
            "advice": items, "latest_general_judgment": general[-1] if general else None,
            "history": [{**r, "applies_to_current_revision": r['version'] == revision.version} for r in judgments],
            "notice": "People may accept, reject, modify or defer advice and record a later review. Acceptance records a judgment only; it does not execute actions or grant permissions."}
