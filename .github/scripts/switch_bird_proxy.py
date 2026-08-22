from pathlib import Path

path = Path('index.html')
s = path.read_text()
worker = 'https://firstlight-bird-proxy.kiah-harpool.workers.dev'

old_keys_html = '''
    <details class="keys">
      <summary>API keys (required once)</summary>
      <div class="keys-fields">
        <input id="key-ebird" type="text" placeholder="eBird API key">
        <input id="key-xc" type="text" placeholder="Xeno-canto API key">
        <p class="keys-hint">
          Free keys — eBird: <a href="https://ebird.org/api/keygen" target="_blank" rel="noopener">ebird.org/api/keygen</a>.
          Xeno-canto: register at <a href="https://xeno-canto.org" target="_blank" rel="noopener">xeno-canto.org</a>, key is on your account page.
          Kept only in this browser, on this device — nothing is sent anywhere but eBird and Xeno-canto.
        </p>
      </div>
    </details>
'''
if old_keys_html not in s:
    raise SystemExit('Could not find API key settings block')
s = s.replace(old_keys_html, '', 1)

anchor = "const FADE_SECONDS = 2.5;\n"
if anchor not in s:
    raise SystemExit('Could not find proxy constant anchor')
s = s.replace(anchor, anchor + f"const BIRD_PROXY_URL = '{worker}';\n", 1)

old_key_state = '''const stageLocationEl = document.getElementById('stage-location');
const keyEbird = document.getElementById('key-ebird');
const keyXC = document.getElementById('key-xc');

// ---------- Remember API keys on this device ----------
keyEbird.value = localStorage.getItem('firstlight_ebird_key') || '';
keyXC.value = localStorage.getItem('firstlight_xc_key') || '';
keyEbird.addEventListener('input', () => localStorage.setItem('firstlight_ebird_key', keyEbird.value.trim()));
keyXC.addEventListener('input', () => localStorage.setItem('firstlight_xc_key', keyXC.value.trim()));
'''
new_key_state = '''const stageLocationEl = document.getElementById('stage-location');
try{
  localStorage.removeItem('firstlight_ebird_key');
  localStorage.removeItem('firstlight_xc_key');
}catch(e){}
'''
if old_key_state not in s:
    raise SystemExit('Could not find browser key storage block')
s = s.replace(old_key_state, new_key_state, 1)

old_start = '''async function startChorus(lat, lng){
  const ebirdKey = keyEbird.value.trim();
  const xcKey = keyXC.value.trim();
  if(!ebirdKey || !xcKey){
    setStatus('Add both API keys below first — they\\'re free and take a minute.');
    return;
  }

  currentCoords = { lat, lng };
'''
new_start = '''async function startChorus(lat, lng){
  currentCoords = { lat, lng };
'''
if old_start not in s:
    raise SystemExit('Could not find startChorus key guard')
s = s.replace(old_start, new_start, 1)
s = s.replace('const species = await fetchNearbySpecies(lat, lng, ebirdKey);', 'const species = await fetchNearbySpecies(lat, lng);', 1)
s = s.replace('const withAudio = await attachRecordings(picked, xcKey);', 'const withAudio = await attachRecordings(picked);', 1)

old_ebird = '''async function fetchNearbySpecies(lat, lng, ebirdKey){
  const url = `https://api.ebird.org/v2/data/obs/geo/recent?lat=${lat}&lng=${lng}&dist=25&back=14`;
  const res = await fetch(url, { headers: { 'X-eBirdApiToken': ebirdKey } });
'''
new_ebird = '''async function fetchNearbySpecies(lat, lng){
  const url = `${BIRD_PROXY_URL}/ebird/recent?lat=${encodeURIComponent(lat)}&lng=${encodeURIComponent(lng)}`;
  const res = await fetch(url, { headers: { 'Accept': 'application/json' } });
'''
if old_ebird not in s:
    raise SystemExit('Could not find direct eBird request')
s = s.replace(old_ebird, new_ebird, 1)

old_attach_head = 'async function attachRecordings(species, xcKey){'
if old_attach_head not in s:
    raise SystemExit('Could not find attachRecordings signature')
s = s.replace(old_attach_head, 'async function attachRecordings(species){', 1)

old_xeno = '''      const q = encodeURIComponent(`sp:\"${bird.sciName}\"`);
      const url = `https://xeno-canto.org/api/3/recordings?query=${q}&key=${xcKey}&per_page=10`;
      const res = await fetch(url);
'''
new_xeno = '''      const url = `${BIRD_PROXY_URL}/xeno/recordings?sciName=${encodeURIComponent(bird.sciName)}`;
      const res = await fetch(url, { headers: { 'Accept': 'application/json' } });
'''
if old_xeno not in s:
    raise SystemExit('Could not find direct Xeno-canto request')
s = s.replace(old_xeno, new_xeno, 1)

old_shared_guard = '''async function startSharedChorus(birds){
  if(!keyXC.value.trim()){
    setStatus('Add a Xeno-canto key below to hear this shared chorus.');
    return;
  }
  stopAll();
'''
new_shared_guard = '''async function startSharedChorus(birds){
  stopAll();
'''
if old_shared_guard not in s:
    raise SystemExit('Could not find shared chorus key guard')
s = s.replace(old_shared_guard, new_shared_guard, 1)
s = s.replace('const withAudio = await attachRecordings(birds, keyXC.value.trim());', 'const withAudio = await attachRecordings(birds);', 1)

for forbidden in [
    'keyEbird',
    'keyXC',
    'firstlight_ebird_key',
    'firstlight_xc_key',
    'https://api.ebird.org',
    'https://xeno-canto.org/api/3/recordings',
    'X-eBirdApiToken',
    'xcKey',
    'ebirdKey',
]:
    if forbidden in s:
        raise SystemExit(f'Browser credential or direct API reference still present: {forbidden}')

if worker not in s:
    raise SystemExit('First Light Worker URL was not added')

path.write_text(s)
