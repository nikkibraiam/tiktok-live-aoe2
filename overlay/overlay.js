const socket = io("http://localhost:5000");

// --------------------
// CONFIG
// --------------------
const giftToVM = {
  // VM1 - AZUL
  "TikTok": "vm1",
  "White Rose": "vm1",
  "Ice Cream Cone": "vm1",
  "Finger Heart": "vm1",
  "Heart Me": "vm1",
  "Doughnut": "vm1",
  "Cap": "vm1",
  "Mishka Bear": "vm1",
  "Sunglasses": "vm1",
  "Money Gun": "vm1",
  "Galaxy": "vm1",

  // VM2 - ROJO
  "You're awesome": "vm2",
  "I'm Ready": "vm2",
  "GG": "vm2",
  "Rosa": "vm2",
  "Perfume": "vm2",
  "Capybara": "vm2",
  "Hat and Mustache": "vm2",
  "Hand Hearts": "vm2",
  "Hearts": "vm2",
  "Gem Gun": "vm2",
  "Shiny air balloon": "vm2"
};

const unitCounters = {
  vm1: {},
  vm2: {}
};

const donors = {}; // user -> total units

// --------------------
// SOCKET EVENTS
// --------------------
socket.on("overlay", (data) => {
  const { user, gift, amount } = data;
  const vm = giftToVM[gift];
  if (!vm) return;

  // FEED
  spawnFeed(user, gift, amount, vm);

  // UNITS
  addUnits(vm, gift, amount);

  // DONORS
  donors[user] = (donors[user] || 0) + amount;
  updateTop();
});

// --------------------
// UI FUNCTIONS
// --------------------
function addUnits(vm, gift, amount) {
  const unit = gift; // simplificado visual
  unitCounters[vm][unit] = (unitCounters[vm][unit] || 0) + amount;
  renderUnits(vm);
}

function renderUnits(vm) {
  const container = document.getElementById(`units-${vm}`);
  container.innerHTML = "";

  Object.entries(unitCounters[vm]).forEach(([unit, count]) => {
    const div = document.createElement("div");
    div.className = "unit";
    div.innerHTML = `
      <img src="units/${unit[0].toLowerCase()}.png">
      <div>${count}</div>
    `;
    container.appendChild(div);
  });
}

function spawnFeed(user, gift, amount, vm) {
  const feed = document.getElementById("feed");
  const el = document.createElement("div");
  el.className = "event";
  el.innerHTML = `
    <b>${user}</b> envió 🎁 ${gift} x${amount}
    <br><small>${vm === "vm1" ? "🔵 AZUL" : "🔴 ROJO"}</small>
  `;
  feed.appendChild(el);

  setTimeout(() => el.remove(), 4500);
}

function updateTop() {
  const list = document.getElementById("top-list");
  list.innerHTML = "";

  Object.entries(donors)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .forEach(([user, count], i) => {
      const li = document.createElement("li");
      li.innerHTML = `${i === 0 ? "👑" : "⚔️"} ${user} — ${count}`;
      list.appendChild(li);
    });
}
