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
  const { gift, amount, user, avatar, diamonds } = data;

  const resolved = resolveGift(gift);
  if (!resolved) return;

  const { vm, action, unit } = resolved;

  if (!donors[vm][user]) {
    donors[vm][user] = {
      name: user.slice(0, 20),
      avatar: avatar || "overlay/default_avatar.png",
      total: 0,
      units: {}
    };
  }

  const donor = donors[vm][user];
  donor.total += amount * diamonds;
  const unitKey = `${action}_${unit}`;
  donor.units[unitKey] = (donor.units[unitKey] || 0) + amount;
  updatePower(vm, amount * diamonds);
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
// POWER BAR
// --------------------
function updatePower(vm, amount) {
  power[vm] += amount;

  const total = power.vm1 + power.vm2 || 1;
  const bluePct = (power.vm1 / total) * 100;
  const redPct  = (power.vm2 / total) * 100;

  const blueBar = document.getElementById("blue-power");
  const redBar  = document.getElementById("red-power");
  const bluePoints = document.getElementById("blue-points");
  const redPoints  = document.getElementById("red-points");

  blueBar.style.width = `${bluePct}%`;
  redBar.style.width  = `${redPct}%`;

  bluePoints.textContent = power.vm1 + " PTS";
  redPoints.textContent  = power.vm2 + " PTS";

  document.body.classList.toggle("blue-dominates", bluePct > 65);
  document.body.classList.toggle("red-dominates", redPct > 65);
}


function renderTop(vm) {
  const list = document.getElementById(`top-${vm}`);
  list.innerHTML = "";

  Object.values(donors[vm])
    .sort((a, b) => b.total - a.total)
    .slice(0, 5)
    .forEach((donor, i) => {
      const li = document.createElement("li");
      li.className = "top-player";

      const unitsHtml = Object.entries(donor.units)
        .map(([key, count]) => {
          const [action, unit] = key.split("_");
          return `
            <img 
              class="unit-mini" 
              src="overlay/units/${action}/${unit}.webp" 
              title="${unit} x${count}"
            >
          `;
        })
        .join("");

      li.innerHTML = `
        <div class="rank">${i === 0 ? "👑" : i + 1}</div>

        <img class="avatar" src="${donor.avatar}">

        <div class="name">${donor.name}</div>

        <div class="units">
          ${unitsHtml}
        </div>

        <div class="total">${donor.total} pts</div>
      `;

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
