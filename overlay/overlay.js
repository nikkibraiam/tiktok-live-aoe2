const socket = io("http://localhost:5000");

const giftMaps = {};
const unitCounters = { vm1: {}, vm2: {} };
let power = { vm1: 0, vm2: 0 };
const donors = {
  vm1: {}, // user -> total
  vm2: {}
};

// --------------------
// LOAD GIFTMAPS
// --------------------
async function loadGiftMaps() {
  giftMaps.vm1 = await fetch("/vm1/gift_map.json").then(r => r.json());
  giftMaps.vm2 = await fetch("/vm2/gift_map.json").then(r => r.json());

  renderInfoBar("vm1");
  renderInfoBar("vm2");
}

loadGiftMaps();

// --------------------
// SOCKET EVENT
// --------------------
socket.on("overlay", data => {
  const { gift, amount, user } = data;

  const resolved = resolveGift(gift);
  if (!resolved) return;

  const { vm, action, unit } = resolved;

  addUnit(vm, action, unit, gift, amount);
  updatePower(vm, amount);

donors[vm][user] = (donors[vm][user] || 0) + amount;
  renderTop(vm);
});

// --------------------
// RESOLUTION
// --------------------
function resolveGift(giftName) {
  for (const vm of ["vm1", "vm2"]) {
    const entry = giftMaps[vm]?.find(g => g.gift === giftName);
    if (entry) {
      return {
        vm,
        action: entry.army.action,
        unit: entry.army.unit
      };
    }
  }
  return null;
}

// --------------------
// UNIT HANDLING
// --------------------
function addUnit(vm, action, unit, gift, amount) {
  const key = `${action}_${unit}`;
  unitCounters[vm][key] = (unitCounters[vm][key] || 0) + amount;

  renderUnits(vm, action, unit, gift, unitCounters[vm][key]);
}

function renderUnits(vm, action, unit, gift, count) {
  const container = document.getElementById(`units-${vm}`);
  let card = container.querySelector(`[data-key="${action}_${unit}"]`);

  if (!card) {
    card = document.createElement("div");
    card.className = "unit";
    card.dataset.key = `${action}_${unit}`;

    card.innerHTML = `
      <img src="overlay/units/${action}/${unit}.webp">
      <img class="gift" src="overlay/gifts/${gift}.webp">
      <div class="count">x${count}</div>
    `;
    container.appendChild(card);
  } else {
    card.querySelector(".count").innerText = `x${count}`;
    card.querySelector(".gift").src = `gifts/${gift}.webp`;
  }
}

// --------------------
// POWER BAR
// --------------------
function updatePower(vm, amount) {
  power[vm] += amount;

  const total = power.vm1 + power.vm2 || 1;
  const bluePct = (power.vm1 / total) * 100;
  const redPct  = (power.vm2 / total) * 100;

  blueBar.style.width = `${bluePct}%`;
  redBar.style.width  = `${redPct}%`;

  document.body.classList.toggle("blue-dominates", bluePct > 65);
  document.body.classList.toggle("red-dominates", redPct > 65);
}

function renderTop(vm) {
  const list = document.getElementById(`top-${vm}`);
  list.innerHTML = "";

  Object.entries(donors[vm])
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .forEach(([user, total], i) => {
      const li = document.createElement("li");
      li.innerHTML = `${i === 0 ? "👑" : "⚔️"} ${user} (${total})`;
      list.appendChild(li);
    });
}


function killRandomUnit(vm) {
  const enemy = vm === "vm1" ? "vm2" : "vm1";
  const keys = Object.keys(unitCounters[enemy]);
  if (!keys.length) return;

  const randomKey = keys[Math.floor(Math.random() * keys.length)];
  unitCounters[enemy][randomKey]--;

  if (unitCounters[enemy][randomKey] <= 0) {
    delete unitCounters[enemy][randomKey];
  }

  explodeUnit(enemy, randomKey);
  renderAllUnits(enemy);
}

function explodeUnit(vm, key) {
  const el = document.querySelector(`#units-${vm} [data-key="${key}"]`);
  if (!el) return;

  el.classList.add("explode");
  setTimeout(() => el.remove(), 400);
}

function renderInfoBar(vm) {
  const container = document.getElementById(`info-${vm}`);
  container.innerHTML = "";

  giftMaps[vm].forEach(entry => {
    const { gift, army } = entry;

    const el = document.createElement("div");
    el.className = "info-unit";

    el.innerHTML = `
      <img 
        class="unit-img" 
        src="overlay/units/${army.action}/${army.unit}.webp"
        title="${army.unit}"
      >
      <img 
        class="gift-img" 
        src="overlay/gifts/${gift}.webp"
        title="${gift}"
      >
    `;

    container.appendChild(el);
  });
}
