const socket = io("http://localhost:5000");

const giftMaps = {};
const unitCounters = { vm1: {}, vm2: {} };
let power = { vm1: 0, vm2: 0 };
const avatarCache = {}; // user_id -> true | false
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
socket.on("avatar_ready", data => {
  const { user_id, avatar } = data;

  ["vm1", "vm2"].forEach(vm => {
    const donor = donors[vm]?.[user_id];
    if (!donor) return;

    // ⛔ Ya tiene avatar real
    if (!donor.avatar.includes("default_avatar")) return;

    donor.avatar = avatar + "?t=" + Date.now();

    const img = document.querySelector(
      `img.avatar[data-user-id="${user_id}"]`
    );

    if (img) img.src = donor.avatar;

    console.log("🖼️ Avatar actualizado:", user_id);
  });
});


socket.on("overlay", data => {
  const {
    gift,
    vm: directVm,
    action: directAction,
    unit: directUnit,
    amount,
    diamonds = 1,
    user,
    user_id
  } = data;

  let vm, action, unit;

  // 🎁 CASO GIFT
  if (gift) {
    const resolved = resolveGift(gift);
    if (!resolved) return;
    ({ vm, action, unit } = resolved);
  } 
  // 💬❤️➕ CASO COMMENT / LIKE / FOLLOW / SHARE
  else {
    if (!directVm || !directAction || !directUnit) return;
    vm = directVm;
    action = directAction;
    unit = directUnit;
  }

  // --------------------
  // UNIDAD EN PANTALLA
  // --------------------
  createUnit(vm, action, unit, user);

  // --------------------
  // DONOR
  // --------------------
  if (!donors[vm][user_id]) {
    donors[vm][user_id] = {
      id: user_id,
      name: user.slice(0, 20),
      avatar: "overlay/default_avatar.png",
      total: 0,
      units: {}
    };
  }

    const donor = donors[vm][user_id];
    const points = amount * diamonds;

    donor.total += points;

    const unitKey = `${action}_${unit}`;
    donor.units[unitKey] = (donor.units[unitKey] || 0) + amount;

    // --------------------
    // POWER + TOP
    // --------------------
    updatePower(vm, points);
    
    checkAvatarExists(user_id).then(url => {
      if(url){
        donors[vm][user_id].avatar = url;
      }
      renderTop(vm);
    });
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

  animateBar(blueBar, bluePct);
  animateBar(redBar, redPct);

  bluePoints.textContent = power.vm1.toLocaleString('es-CO') + " PTS";
  redPoints.textContent  = power.vm2.toLocaleString('es-CO') + " PTS";

  document.body.classList.toggle("blue-dominates", bluePct > 65);
  document.body.classList.toggle("red-dominates", redPct > 65);
}

// Función para animar progresivamente
function animateBar(bar, targetPct) {
  let current = parseFloat(bar.style.width) || 0;
  const step = (targetPct - current) / 20; // divide en 20 pasos
  let i = 0;

  const interval = setInterval(() => {
    if (i >= 20) {
      bar.style.width = `${targetPct}%`;
      clearInterval(interval);
      return;
    }
    current += step;
    bar.style.width = `${current}%`;
    i++;
  }, 25); // cada 25ms → ~0.5s total
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

      // const unitsHtml = Object.entries(donor.units)
      //   .map(([key, count]) => {
      //     const [action, unit] = key.split("_");
      //     return `
      //       <img 
      //         class="unit-mini" 
      //         src="overlay/units/${action}/${unit}.webp" 
      //         title="${unit} x${count}"
      //       >
      //     `;
      //   })
      //   .join("");
      let rank = "👑";
      if (i == 0){
        rank = "👑";
      }else if (i == 1){
        rank = "🥈";
      }
      else if (i == 2){
        rank = "🥉";
      }
      else{
        rank = "‼️";
      }

      li.innerHTML = `
        <div class="rank">${rank}</div>

        <img class="avatar" data-user-id="${donor.id}" src="${donor.avatar}">

        <div class="name">${donor.name}</div>

        <div class="total">${formatNumberShort(donor.total)} pts</div>

      `;

      list.appendChild(li);
    });
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
        class="unit-img ${vm}" 
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


function createUnit(vm, action, unit, user) {
  const queueContainer = document.getElementById(`queue-${vm}`);

  const RADIUS = 49;
  const TOTAL_TIME = 20;
  const totalDash = 2 * Math.PI * RADIUS;

  const queueUnit = document.createElement("div");
  queueUnit.className = "queue-unit";

  queueUnit.innerHTML = `
    <img class="unit-img ${vm}" src="overlay/units/${action}/${unit}.webp">

    <div class="unit-user">${user}</div>

    <svg width="100" height="100">
      <circle
        cx="50"
        cy="50"
        r="${RADIUS}"
        stroke="white"
        stroke-width="4"
        fill="transparent"
        stroke-dasharray="${totalDash}"
        stroke-dashoffset="${totalDash}">
      </circle>
    </svg>

    <div class="countdown">${TOTAL_TIME}</div>
  `;

  queueContainer.appendChild(queueUnit);

  const circle = queueUnit.querySelector("circle");
  const countdownEl = queueUnit.querySelector(".countdown");

  let time = TOTAL_TIME;

  const interval = setInterval(() => {
    time -= 0.1;

    if (time <= 0) {
      clearInterval(interval);
      countdownEl.textContent = "0";

      const key = `${action}_${unit}`;
      unitCounters[vm][key] = (unitCounters[vm][key] || 0) + 1;

      queueUnit.remove();
      return;
    }

    countdownEl.textContent = Math.ceil(time);
    circle.style.strokeDashoffset = (time / TOTAL_TIME) * totalDash;
  }, 100);
}



function formatNumberShort(num) {
  if (num >= 1e12) return (num / 1e12).toFixed(1) + "T";
  if (num >= 1e9)  return (num / 1e9).toFixed(1) + "G";
  if (num >= 1e6)  return (num / 1e6).toFixed(1) + "M";
  if (num >= 1e3)  return (num / 1e3).toFixed(1) + "K";
  return num.toString();
}

function checkAvatarExists(userId) {
  if (avatarCache[userId] !== undefined) {
    return Promise.resolve(
      avatarCache[userId]
        ? `/overlay/avatars/${userId}.jpeg`
        : null
    );
  }

  return new Promise(resolve => {
    const img = new Image();
    const url = `/overlay/avatars/${userId}.jpeg?t=${Date.now()}`;

    img.onload = () => {
      avatarCache[userId] = true;
      resolve(url);
    };

    img.onerror = () => {
      avatarCache[userId] = false;
      resolve(null);
    };

    img.src = url;
  });
}

