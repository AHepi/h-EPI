# WHAT THIS FILE DOES, IN PLAIN WORDS
#
# Opens "16 Sonnet page.html" in a headless browser at phone size, catches every request the page
# sends to Sonnet, and answers with a stand-in (the same "one piece short" stand-in as
# "16 Sonnet guesser tests.js"). Presses Run, waits for the end, and checks the results box.
# Then checks the page stops cleanly when Sonnet can't be reached. Saves screenshots next to it.
# Run with:  python3 "16 page test in a browser.py"
import os
import json, pathlib, subprocess, sys
from playwright.sync_api import sync_playwright

here = pathlib.Path(__file__).parent
page_file = (here / '16 Sonnet page.html').resolve()
worlds = json.loads(subprocess.check_output(['node', '-e', "process.stdout.write(JSON.stringify(require('./03 test worlds.js')))"], cwd=here))

def short_model(w):
    if w['id'] == 'hidden-ball':
        return {'things': {'screen': w['world']['things']['screen'], 'seen': w['world']['things']['seen']}, 'events': [], 'start': {'screen': 'down', 'seen': 'at 1'},
                'rules': [{'name': 'a', 'when': ['seen is at 1'], 'then': 'seen is at 2'}, {'name': 'b', 'when': ['seen is at 2'], 'then': 'seen is at 3'},
                          {'name': 'c', 'when': ['seen is at 3'], 'then': 'seen is at 4'}, {'name': 'hide', 'when': ['seen is at 1', 'screen is up'], 'then': 'seen is nothing'},
                          {'name': 'reappear', 'when': ['seen is nothing'], 'then': 'seen is at 4'}]}
    m = dict(w['world']); m['rules'] = w['world']['rules'][:-1]; return m

def missing_piece(w):
    if w['id'] == 'hidden-ball':
        return {'new_things': {'place': w['world']['things']['place']}, 'new_start': {'place': '1'}, 'new_rules': w['world']['rules']}
    return {'new_things': {}, 'new_start': {}, 'new_rules': [w['world']['rules'][-1]]}

seen_requests = []
def stand_in(route):
    body = json.loads(route.request.post_data)
    seen_requests.append(body)
    w = next(x for x in worlds if x['request'] in body['messages'][0]['content'])
    reply = missing_piece(w) if 'Write only the new parts' in body['messages'][-1]['content'] else short_model(w)
    text = 'Here it is:\n```json\n' + json.dumps(reply) + '\n```'
    route.fulfill(status=200, content_type='application/json', body=json.dumps({'content': [{'type': 'text', 'text': text}], 'stop_reason': 'end_turn'}))

failed = 0
def expect_that(name, ok, detail=''):
    global failed
    if not ok: failed += 1
    print(('ok   ' if ok else 'FAIL ') + name + ('' if ok or not detail else '\n     ' + str(detail)))

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get("BROWSER_PATH") or None)
    for scheme in ['light', 'dark']:
        page = browser.new_page(viewport={'width': 390, 'height': 844}, device_scale_factor=2, color_scheme=scheme)
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.route('https://api.anthropic.com/**', stand_in)
        page.goto(page_file.as_uri())
        expect_that(f'[{scheme}] the page loads with no code errors', not errors, errors)
        expect_that(f'[{scheme}] the page offers all five worlds', page.locator('#which option').count() == 6)
        page.screenshot(path=str(here / f'16 screenshot - before the run - {scheme}.png'), full_page=True)
        if scheme == 'dark':
            page.close(); continue
        page.click('#run')
        page.wait_for_function("document.getElementById('results').value.length > 0", timeout=240000)
        results = json.loads(page.input_value('#results'))
        expect_that('the run finishes all five worlds, four ways each', len(results['summary']) == 20, results['summary'])
        expect_that('no world stopped', not any('stopped' in s for s in results['summary']), results['summary'])
        hidden = next(w for w in results['worlds'] if w['world'] == 'hidden-ball')
        expect_that('hidden ball, guess and fix: every shown job passes after a new part', hidden['ways']['guess and fix']['final']['original_seen_passed'] == 5, hidden['ways']['guess and fix']['rounds'])
        expect_that('requests to Sonnet go to Sonnet 4.6 with the guide as standing instructions', all(b['model'] == 'claude-sonnet-4-6' and b.get('system') for b in seen_requests))
        expect_that('the counts shown match the requests sent', f"Requests to Sonnet: {len(seen_requests)}." in page.inner_text('#counts'), page.inner_text('#counts'))
        expect_that('no code errors during the run', not errors, errors)
        page.click('#copy')
        page.wait_for_timeout(300)
        expect_that('the copy button answers', page.inner_text('#copied') in ('Copied.', 'Selected. Use your device’s Copy.'), page.inner_text('#copied'))
        page.screenshot(path=str(here / '16 screenshot - after a stand-in run, not Sonnet - light.png'), full_page=True)
        print('\n'.join('   ' + s for s in results['summary']))
        page.close()

    # Sonnet can't be reached: the page should stop cleanly and say so.
    page = browser.new_page(viewport={'width': 390, 'height': 844})
    page.route('https://api.anthropic.com/**', lambda route: route.fulfill(status=403, content_type='application/json', body=json.dumps({'error': {'message': 'not allowed here'}})))
    page.goto(page_file.as_uri())
    page.click('#run')
    page.wait_for_function("document.getElementById('results').value.length > 0", timeout=60000)
    now = page.inner_text('#now')
    expect_that('when Sonnet cannot be reached, the page stops and says why', now.startswith('Stopped:') and 'code 403' in now, now)
    browser.close()

print(f'\n{failed} test(s) failed.')
sys.exit(1 if failed else 0)
