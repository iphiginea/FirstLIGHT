from pathlib import Path

path = Path('index.html')
text = path.read_text()

def replace_once(old, new, label):
    global text
    if old not in text:
        raise SystemExit(f'Missing anchor: {label}')
    text = text.replace(old, new, 1)

# 1) Styling for rare visitors + persistent collection panel.
replace_once(
"""  .controls{ display:flex; gap:.8rem; justify-content:center; flex-wrap:wrap; margin-top:1rem; }
  .controls button{ font-size:.85rem; padding:.7rem 1.5rem; }

  .hidden{ display:none !important; }
""",
"""  .rarity-badge{
    display:inline-block;
    margin-top:.28rem;
    font-family:'IBM Plex Mono', monospace;
    font-size:.61rem;
    letter-spacing:.08em;
    text-transform:uppercase;
    color:var(--gold);
  }
  .bird-card.rare-bird{
    border-color:color-mix(in srgb, var(--gold) 48%, transparent);
    background:color-mix(in srgb, var(--gold) 8%, transparent);
  }

  .controls{ display:flex; gap:.8rem; justify-content:center; flex-wrap:wrap; margin-top:1rem; }
  .controls button{ font-size:.85rem; padding:.7rem 1.5rem; }

  .collection-panel{
    margin:1.25rem auto 0;
    width:100%;
    max-width:520px;
    padding:1.15rem 1.2rem;
    border:1px solid color-mix(in srgb, var(--gold) 28%, transparent);
    border-radius:14px;
    background:color-mix(in srgb, var(--ink) 72%, transparent);
    text-align:left;
  }
  .collection-panel h2{
    margin:0 0 .35rem;
    font-family:'Fraunces', serif;
    font-size:1.15rem;
    font-weight:400;
    font-style:italic;
  }
  .collection-note{
    margin:0 0 .9rem;
    color:var(--feather);
    font-size:.72rem;
    line-height:1.5;
  }
  .collection-list{ display:flex; flex-direction:column; gap:.55rem; }
  .collection-item{
    display:flex;
    justify-content:space-between;
    gap:1rem;
    padding:.65rem .75rem;
    border-radius:10px;
    background:color-mix(in srgb, var(--mist) 5%, transparent);
  }
  .collection-item strong{
    display:block;
    font-family:'Fraunces', serif;
    font-weight:400;
  }
  .collection-item small{
    display:block;
    margin-top:.1rem;
    color:var(--feather);
    font-family:'IBM Plex Mono', monospace;
    font-size:.62rem;
  }
  .collection-date{
    flex:none;
    color:var(--gold);
    font-family:'IBM Plex Mono', monospace;
    font-size:.6rem;
    text-align:right;
  }

  .hidden{ display:none !important; }
""",
"collection styles"
)

# 2) Add the rare-find collection control and panel.
replace_once(
"""    <button id=\"btn-postcard\">View postcard</button>
    <button id=\"btn-reset\">Change location</button>
  </div>

  <div class=\"postcard hidden\" id=\"postcard\">""",
"""    <button id=\"btn-postcard\">View postcard</button>
    <button id=\"btn-collection\">Rare finds · 0</button>
    <button id=\"btn-reset\">Change location</button>
  </div>

  <div class=\"collection-panel hidden\" id=\"collection-panel\">
    <h2>Rare finds</h2>
    <p class=\"collection-note\">Uncommon local visitors you have encountered in a First Light chorus on this device.</p>
    <div class=\"collection-list\" id=\"collection-list\"></div>
  </div>

  <div class=\"postcard hidden\" id=\"postcard\">""",
"collection markup"
)

# 3) Persistent collection state.
replace_once(
"""let placeLabel = '';
const EXCLUDED_SPECIES = new Set(['Turkey Vulture', 'Blue Jay']);
const FADE_SECONDS = 2.5;
""",
"""let placeLabel = '';
let rareCollection = loadRareCollection();
const EXCLUDED_SPECIES = new Set(['Turkey Vulture', 'Blue Jay']);
const FADE_SECONDS = 2.5;
const RARE_VISITOR_CHANCE = 0.08;
const MAX_PLAUSIBLE_RARE_DISTANCE_KM = 12;
const MAX_PLAUSIBLE_RARE_AGE_DAYS = 7;
""",
"rarity state"
)

# 4) Collection button behavior.
replace_once(
"""document.getElementById('btn-postcard').addEventListener('click', openPostcard);
document.getElementById('btn-postcard-close').addEventListener('click', () => document.getElementById('postcard').classList.add('hidden'));
""",
"""document.getElementById('btn-postcard').addEventListener('click', openPostcard);
document.getElementById('btn-collection').addEventListener('click', () => {
  const panel = document.getElementById('collection-panel');
  panel.classList.toggle('hidden');
  if(!panel.classList.contains('hidden')) renderRareCollection();
});
document.getElementById('btn-postcard-close').addEventListener('click', () => document.getElementById('postcard').classList.add('hidden'));
""",
"collection event"
)

replace_once(
"""  chorusEl.style.display = 'none';
  chorusEl.innerHTML = '';
  setSkyProgress(0);
""",
"""  chorusEl.style.display = 'none';
  chorusEl.innerHTML = '';
  document.getElementById('collection-panel').classList.add('hidden');
  setSkyProgress(0);
""",
"reset collection panel"
)

# 5) Save rare finds only after a bird has a usable recording and appears in the chorus.
replace_once(
"""    currentSpecies = usable;
    stageLocationEl.classList.add('hidden');
    renderCards(usable);
""",
"""    currentSpecies = usable;
    collectRareVisitors(usable);
    updateCollectionButton();
    stageLocationEl.classList.add('hidden');
    renderCards(usable);
""",
"collect rare visitors"
)

# 6) Replace city-wide randomization with distance/frequency/recency weighting.
old_core = """async function fetchNearbySpecies(lat, lng){
  const url = `${BIRD_PROXY_URL}/ebird/recent?lat=${encodeURIComponent(lat)}&lng=${encodeURIComponent(lng)}`;
  const res = await fetch(url, { headers: { 'Accept': 'application/json' } });
  if(!res.ok) throw new Error('eBird request failed: ' + res.status);
  const data = await res.json();
  const bySpecies = {};
  data.forEach(obs => {
    if(!bySpecies[obs.speciesCode] || obs.obsDt > bySpecies[obs.speciesCode].obsDt){
      bySpecies[obs.speciesCode] = obs;
    }
  });
  return Object.values(bySpecies)
    .filter(o => !EXCLUDED_SPECIES.has(o.comName))
    .map(o => ({
      comName: o.comName,
      sciName: o.sciName,
      speciesCode: o.speciesCode,
      obsDt: o.obsDt
    }));
}

function pickFive(species){
  const sorted = [...species].sort((a,b) => new Date(b.obsDt) - new Date(a.obsDt));
  const pool = sorted.slice(0, Math.max(15, Math.min(sorted.length, 40)));
  const shuffled = pool.sort(() => Math.random() - 0.5);
  return shuffled.slice(0, 5);
}
"""
new_core = """function distanceKm(lat1, lng1, lat2, lng2){
  if(!Number.isFinite(lat2) || !Number.isFinite(lng2)) return null;
  const toRad = d => d * Math.PI / 180;
  const R = 6371;
  const dLat = toRad(lat2 - lat1);
  const dLng = toRad(lng2 - lng1);
  const a = Math.sin(dLat/2) ** 2 + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng/2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

function ageDays(obsDt){
  if(!obsDt) return 99;
  const parsed = new Date(obsDt.replace(' ', 'T'));
  if(Number.isNaN(parsed.getTime())) return 99;
  return Math.max(0, (Date.now() - parsed.getTime()) / 86400000);
}

async function fetchNearbySpecies(lat, lng){
  const url = `${BIRD_PROXY_URL}/ebird/recent?lat=${encodeURIComponent(lat)}&lng=${encodeURIComponent(lng)}`;
  const res = await fetch(url, { headers: { 'Accept': 'application/json' } });
  if(!res.ok) throw new Error('eBird request failed: ' + res.status);
  const data = await res.json();
  const bySpecies = {};

  data.forEach(obs => {
    if(EXCLUDED_SPECIES.has(obs.comName)) return;
    const code = obs.speciesCode;
    if(!bySpecies[code]){
      bySpecies[code] = {
        comName: obs.comName,
        sciName: obs.sciName,
        speciesCode: code,
        obsDt: obs.obsDt,
        reportCount: 0,
        nearestKm: Infinity
      };
    }
    const bird = bySpecies[code];
    bird.reportCount += 1;
    if(obs.obsDt > bird.obsDt) bird.obsDt = obs.obsDt;
    const d = distanceKm(lat, lng, Number(obs.lat), Number(obs.lng));
    if(d !== null) bird.nearestKm = Math.min(bird.nearestKm, d);
  });

  const birds = Object.values(bySpecies);
  birds.forEach(bird => {
    if(!Number.isFinite(bird.nearestKm)) bird.nearestKm = 25;
    bird.ageDays = ageDays(bird.obsDt);
  });
  return birds;
}

function weightedPick(pool, weightFn){
  if(!pool.length) return null;
  const weights = pool.map(b => Math.max(0.01, weightFn(b)));
  let roll = Math.random() * weights.reduce((a,b) => a+b, 0);
  for(let i=0;i<pool.length;i++){
    roll -= weights[i];
    if(roll <= 0) return pool[i];
  }
  return pool[pool.length - 1];
}

function normalWeight(bird){
  const distance = Math.max(0.5, bird.nearestKm);
  const recency = Math.max(0, 14 - bird.ageDays);
  return (1 + Math.log2(1 + bird.reportCount) * 2.4) * (1 + recency / 10) / Math.pow(distance, 0.65);
}

function pickFive(species){
  if(species.length <= 5) return species.map(b => ({ ...b, rarity: 'regular' }));

  const counts = species.map(b => b.reportCount).sort((a,b) => a-b);
  const medianReports = counts[Math.floor(counts.length / 2)] || 1;
  const rareCandidates = species.filter(b =>
    b.nearestKm <= MAX_PLAUSIBLE_RARE_DISTANCE_KM &&
    b.ageDays <= MAX_PLAUSIBLE_RARE_AGE_DAYS &&
    b.reportCount <= Math.max(1, Math.floor(medianReports * 0.5))
  );

  const chosen = [];
  const used = new Set();
  const includeRare = rareCandidates.length > 0 && Math.random() < RARE_VISITOR_CHANCE;

  if(includeRare){
    const rare = weightedPick(rareCandidates, b =>
      (1 + Math.max(0, MAX_PLAUSIBLE_RARE_AGE_DAYS - b.ageDays)) /
      (1 + b.nearestKm) /
      Math.max(1, b.reportCount)
    );
    if(rare){
      chosen.push({ ...rare, rarity: 'rare' });
      used.add(rare.speciesCode);
    }
  }

  const regularPool = species
    .filter(b => !used.has(b.speciesCode))
    .filter(b => b.nearestKm <= 20 || b.reportCount > medianReports)
    .sort((a,b) => normalWeight(b) - normalWeight(a))
    .slice(0, Math.min(28, species.length));

  while(chosen.length < 5 && regularPool.length){
    const bird = weightedPick(regularPool, normalWeight);
    if(!bird) break;
    chosen.push({ ...bird, rarity: 'regular' });
    used.add(bird.speciesCode);
    regularPool.splice(regularPool.findIndex(b => b.speciesCode === bird.speciesCode), 1);
  }

  if(chosen.length < 5){
    species
      .filter(b => !used.has(b.speciesCode))
      .sort((a,b) => normalWeight(b) - normalWeight(a))
      .slice(0, 5 - chosen.length)
      .forEach(b => chosen.push({ ...b, rarity: 'regular' }));
  }

  return chosen;
}
"""
replace_once(old_core, new_core, 'weighted chorus core')

# 7) Rare collection helpers.
replace_once(
"""async function attachRecordings(species){
""",
"""function loadRareCollection(){
  try{
    const raw = localStorage.getItem('firstlight_rare_collection');
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  }catch(e){ return []; }
}

function saveRareCollection(){
  try{ localStorage.setItem('firstlight_rare_collection', JSON.stringify(rareCollection)); }catch(e){}
}

function collectRareVisitors(birds){
  let changed = false;
  birds.filter(b => b.rarity === 'rare').forEach(bird => {
    if(rareCollection.some(item => item.speciesCode === bird.speciesCode)) return;
    rareCollection.push({
      speciesCode: bird.speciesCode,
      comName: bird.comName,
      sciName: bird.sciName,
      firstSeen: new Date().toISOString(),
      place: placeLabel || 'Somewhere near you'
    });
    changed = true;
  });
  if(changed) saveRareCollection();
}

function updateCollectionButton(){
  const btn = document.getElementById('btn-collection');
  if(btn) btn.textContent = `Rare finds · ${rareCollection.length}`;
}

function renderRareCollection(){
  const list = document.getElementById('collection-list');
  list.innerHTML = '';
  if(!rareCollection.length){
    const empty = document.createElement('p');
    empty.className = 'collection-note';
    empty.textContent = 'No rare visitors yet. Keep listening — they only appear occasionally, and only when a recent nearby sighting makes sense.';
    list.appendChild(empty);
    return;
  }
  [...rareCollection].reverse().forEach(item => {
    const row = document.createElement('div');
    row.className = 'collection-item';
    const names = document.createElement('div');
    const common = document.createElement('strong');
    common.textContent = item.comName;
    const scientific = document.createElement('small');
    scientific.textContent = `${item.sciName} · ${item.place}`;
    names.append(common, scientific);
    const date = document.createElement('span');
    date.className = 'collection-date';
    date.textContent = new Date(item.firstSeen).toLocaleDateString(undefined, { month:'short', day:'numeric', year:'numeric' });
    row.append(names, date);
    list.appendChild(row);
  });
}

updateCollectionButton();

async function attachRecordings(species){
""",
"collection helpers"
)

# 8) Mark the rare visitor in the chorus without making it visually loud.
replace_once(
"""    card.className = 'bird-card';
    card.id = 'card-' + bird.speciesCode;
""",
"""    card.className = bird.rarity === 'rare' ? 'bird-card rare-bird' : 'bird-card';
    card.id = 'card-' + bird.speciesCode;
""",
"rare card class"
)

replace_once(
"""    chorusEl.appendChild(card);
  });
""",
"""    if(bird.rarity === 'rare'){
      const nameWrap = card.querySelector('.bird-sci').parentElement;
      const badge = document.createElement('span');
      badge.className = 'rarity-badge';
      badge.textContent = '✦ rare visitor · collected';
      nameWrap.appendChild(badge);
    }
    chorusEl.appendChild(card);
  });
""",
"rare badge"
)

path.write_text(text)
print('Applied weighted local chorus + rare visitor collection patch.')
