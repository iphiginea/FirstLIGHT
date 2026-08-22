from pathlib import Path

path = Path('index.html')
s = path.read_text()

old_card = '''    card.innerHTML = `
      <span class="bird-card-info">
        <span class="pulse"></span>
        <span>
          <span class="bird-name">${bird.comName}</span>
          <span class="bird-sci">${bird.sciName}</span>
        </span>
      </span>
      <button class="mute-btn" data-code="${bird.speciesCode}" aria-label="Mute ${bird.comName}" title="Mute ${bird.comName}">♪</button>
    `;'''
new_card = '''    const info = document.createElement('span');
    info.className = 'bird-card-info';

    const pulse = document.createElement('span');
    pulse.className = 'pulse';

    const names = document.createElement('span');
    const commonName = document.createElement('span');
    commonName.className = 'bird-name';
    commonName.textContent = bird.comName;

    const scientificName = document.createElement('span');
    scientificName.className = 'bird-sci';
    scientificName.textContent = bird.sciName;

    names.append(commonName, scientificName);
    info.append(pulse, names);

    const muteButton = document.createElement('button');
    muteButton.className = 'mute-btn';
    muteButton.dataset.code = bird.speciesCode;
    muteButton.setAttribute('aria-label', `Mute ${bird.comName}`);
    muteButton.title = `Mute ${bird.comName}`;
    muteButton.textContent = '♪';

    card.append(info, muteButton);'''

if old_card not in s:
    raise SystemExit('Bird card render block not found')
s = s.replace(old_card, new_card, 1)

old_postcard = '''  currentSpecies.forEach(b => {
    const li = document.createElement('li');
    li.innerHTML = `${b.comName}<span>${b.sciName}</span>`;
    list.appendChild(li);
  });'''
new_postcard = '''  currentSpecies.forEach(b => {
    const li = document.createElement('li');
    li.appendChild(document.createTextNode(b.comName));
    const scientificName = document.createElement('span');
    scientificName.textContent = b.sciName;
    li.appendChild(scientificName);
    list.appendChild(li);
  });'''

if old_postcard not in s:
    raise SystemExit('Postcard bird render block not found')
s = s.replace(old_postcard, new_postcard, 1)

old_share = '''  try{
    const payload = JSON.parse(decodeURIComponent(atob(encoded)));
    placeLabel = payload.place || 'Somewhere near you';
    currentCoords = { lat: payload.lat, lng: payload.lng };
    const sharedBirds = payload.birds.map(b => ({ comName: b.c, sciName: b.s, speciesCode: b.x, obsDt: '' }));
    window.addEventListener('DOMContentLoaded', () => startSharedChorus(sharedBirds));
    if(document.readyState !== 'loading') startSharedChorus(sharedBirds);
  }catch(e){'''
new_share = '''  try{
    const payload = JSON.parse(decodeURIComponent(atob(encoded)));
    if(!payload || typeof payload !== 'object' || !Array.isArray(payload.birds)){
      throw new Error('Invalid shared chorus payload');
    }
    if(payload.birds.length < 1 || payload.birds.length > 5){
      throw new Error('Invalid shared chorus bird count');
    }

    const lat = Number(payload.lat);
    const lng = Number(payload.lng);
    if(!Number.isFinite(lat) || !Number.isFinite(lng) || lat < -90 || lat > 90 || lng < -180 || lng > 180){
      throw new Error('Invalid shared chorus coordinates');
    }

    const sharedBirds = payload.birds.map(b => {
      if(!b || typeof b !== 'object') throw new Error('Invalid shared bird');
      const comName = typeof b.c === 'string' ? b.c.trim() : '';
      const sciName = typeof b.s === 'string' ? b.s.trim() : '';
      const speciesCode = typeof b.x === 'string' ? b.x.trim() : '';
      if(!comName || comName.length > 120 || !sciName || sciName.length > 120 ||
         !speciesCode || speciesCode.length > 32 || !/^[A-Za-z0-9_-]+$/.test(speciesCode)){
        throw new Error('Invalid shared bird fields');
      }
      return { comName, sciName, speciesCode, obsDt: '' };
    });

    placeLabel = typeof payload.place === 'string' && payload.place.trim() && payload.place.length <= 120
      ? payload.place.trim()
      : 'Somewhere near you';
    currentCoords = { lat, lng };
    window.addEventListener('DOMContentLoaded', () => startSharedChorus(sharedBirds));
    if(document.readyState !== 'loading') startSharedChorus(sharedBirds);
  }catch(e){'''

if old_share not in s:
    raise SystemExit('Shared chorus loader block not found')
s = s.replace(old_share, new_share, 1)

if '${bird.comName}' in s or '${bird.sciName}' in s:
    raise SystemExit('Unsafe bird template interpolation still present')
if 'li.innerHTML = `${b.comName}' in s:
    raise SystemExit('Unsafe postcard HTML still present')

path.write_text(s)
