/* Pixel house shared by the central and the local branch. 160x120, scaled up. */
function drawHouse(ctx, state, highlight, now) {
  const W = 160, H = 120;
  ctx.imageSmoothingEnabled = false;
  ctx.clearRect(0, 0, W, H);
  ctx.fillStyle = "#2a2420";
  ctx.fillRect(0, 0, W, 20);
  const cap = Math.max(0, Math.min(16, Math.floor((state.capacity || 0) / 6)));
  for (let i = 0; i < 16; i++) {
    const lit = i < cap;
    ctx.fillStyle = lit ? "#c46a32" : "#5c5148";
    ctx.fillRect(8 + i * 9, 6, 6, 6);
    if (lit && i + 1 < cap) {
      ctx.fillStyle = "#e7c39a";
      ctx.fillRect(14 + i * 9, 8, 3, 2);
    }
  }
  ctx.fillStyle = "#e4d3bf";
  ctx.fillRect(0, 20, W, 52);
  ctx.fillStyle = "#d3bea4";
  ctx.fillRect(0, 62, W, 8);
  ctx.fillStyle = "#8d6244";
  ctx.fillRect(0, 70, W, 50);
  for (let x = 0; x < W; x += 10) {
    ctx.fillStyle = "#734e36";
    ctx.fillRect(x, 70, 1, 50);
  }
  windowFrame(ctx, 10, 28);
  door(ctx, 138, 36);
  bed(ctx, 8, 74);
  plant(ctx, 142, 58);
  rug(ctx, 62, 96);
  lamp(ctx, 96, 48);
  const nodes = state.nodes || [];
  const byId = {};
  nodes.forEach((n) => { byId[n.id] = n; });
  (state.connections || []).forEach((link) => {
    const a = byId[link.a], b = byId[link.b];
    if (!a || !b) return;
    dash(ctx, a.x + 6, a.y + 6, b.x + 6, b.y + 6, "#3f6b4a");
  });
  nodes.forEach((n) => device(ctx, n, n.id === highlight));
  const pose = state.pose || "idle";
  const bob = Math.floor(now / 280) % 2 === 0 ? 0 : -1;
  if (state.form === "animal") animal(ctx, 76, 104 + bob);
  else person(ctx, 76, 104 + bob, pose);
}

function windowFrame(ctx, x, y) {
  ctx.fillStyle = "#5c3d2e";
  ctx.fillRect(x, y, 28, 20);
  ctx.fillStyle = "#9ec4d4";
  ctx.fillRect(x + 2, y + 2, 10, 7);
  ctx.fillRect(x + 14, y + 2, 10, 7);
  ctx.fillRect(x + 2, y + 11, 10, 7);
  ctx.fillRect(x + 14, y + 11, 10, 7);
  ctx.fillStyle = "#e7e3c9";
  ctx.fillRect(x + 22, y + 4, 2, 2);
}

function bed(ctx, x, y) {
  ctx.fillStyle = "#5c3d2e";
  ctx.fillRect(x, y, 28, 12);
  ctx.fillStyle = "#efe6da";
  ctx.fillRect(x + 2, y + 2, 6, 4);
  ctx.fillStyle = "#8e4a3a";
  ctx.fillRect(x + 10, y + 2, 16, 8);
}

function door(ctx, x, y) {
  ctx.fillStyle = "#5c3d2e";
  ctx.fillRect(x, y, 12, 28);
  ctx.fillStyle = "#8e4a3a";
  ctx.fillRect(x + 2, y + 2, 8, 24);
  ctx.fillStyle = "#e7c39a";
  ctx.fillRect(x + 7, y + 14, 2, 2);
}

function lamp(ctx, x, y) {
  ctx.fillStyle = "#e7c39a";
  ctx.fillRect(x, y, 6, 4);
  ctx.fillStyle = "#5c3d2e";
  ctx.fillRect(x + 2, y + 4, 2, 8);
}

function plant(ctx, x, y) {
  ctx.fillStyle = "#5c3d2e";
  ctx.fillRect(x, y + 10, 6, 5);
  ctx.fillStyle = "#3f6b4a";
  ctx.fillRect(x - 1, y + 4, 8, 6);
  ctx.fillRect(x + 1, y, 4, 5);
}

function rug(ctx, x, y) {
  ctx.fillStyle = "#a33b32";
  ctx.fillRect(x, y, 28, 10);
  ctx.fillStyle = "#e7c39a";
  ctx.fillRect(x + 3, y + 2, 22, 6);
}

function person(ctx, x, y, pose) {
  ctx.fillStyle = "#3a2a22";
  ctx.fillRect(x - 3, y - 18, 6, 2);
  ctx.fillStyle = "#e8c4a4";
  ctx.fillRect(x - 3, y - 16, 6, 6);
  ctx.fillStyle = "#1c1915";
  const look = pose === "look" ? 1 : 0;
  ctx.fillRect(x - 2 + look, y - 14, 1, 1);
  ctx.fillRect(x + 1 + look, y - 14, 1, 1);
  if (pose === "speak") ctx.fillRect(x - 1, y - 12, 2, 1);
  ctx.fillStyle = "#b4532a";
  ctx.fillRect(x - 3, y - 10, 6, 6);
  ctx.fillStyle = "#e8c4a4";
  if (pose === "wave") ctx.fillRect(x + 3, y - 14, 1, 4);
  else ctx.fillRect(x + 3, y - 9, 1, 3);
  ctx.fillRect(x - 4, y - 9, 1, 3);
  ctx.fillStyle = "#3a2a22";
  ctx.fillRect(x - 2, y - 4, 2, 4);
  ctx.fillRect(x, y - 4, 2, 4);
}

function animal(ctx, x, y) {
  ctx.fillStyle = "#c47a3a";
  ctx.fillRect(x - 6, y - 8, 12, 6);
  ctx.fillRect(x + 4, y - 14, 5, 5);
  ctx.fillStyle = "#3a2a22";
  ctx.fillRect(x + 5, y - 12, 1, 1);
  ctx.fillRect(x + 7, y - 12, 1, 1);
  ctx.fillRect(x - 4, y - 2, 2, 2);
  ctx.fillRect(x + 2, y - 2, 2, 2);
}

function device(ctx, node, hot) {
  const x = node.x, y = node.y;
  if (node.kind === "phone") {
    ctx.fillStyle = node.online ? "#241f1b" : "#8a8176";
    ctx.fillRect(x, y, 8, 14);
    ctx.fillStyle = node.online ? "#9ec4d4" : "#d9d0c3";
    ctx.fillRect(x + 1, y + 1, 6, 9);
    if (node.online) {
      ctx.fillStyle = "#1c1915";
      ctx.fillRect(x + 2, y + 3, 1, 1);
      ctx.fillRect(x + 5, y + 3, 1, 1);
    }
  } else {
    ctx.fillStyle = "#5c3d2e";
    ctx.fillRect(x - 2, y + 8, 16, 3);
    ctx.fillStyle = node.online ? "#1c1915" : "#8a8176";
    ctx.fillRect(x, y, 12, 8);
    ctx.fillStyle = node.online ? "#3f6b4a" : "#d9d0c3";
    ctx.fillRect(x + 1, y + 1, 10, 5);
    ctx.fillStyle = "#5c3d2e";
    ctx.fillRect(x + 5, y + 8, 2, 3);
  }
  if (hot) {
    ctx.strokeStyle = "#b4532a";
    ctx.strokeRect(x - 2, y - 2, node.kind === "phone" ? 12 : 16, node.kind === "phone" ? 18 : 14);
  }
}

function dash(ctx, x0, y0, x1, y1, color) {
  const steps = 12;
  ctx.fillStyle = color;
  for (let i = 0; i <= steps; i += 2) {
    const t = i / steps;
    ctx.fillRect(Math.round(x0 + (x1 - x0) * t), Math.round(y0 + (y1 - y0) * t), 2, 2);
  }
}

function mountHouse(canvas, highlight) {
  const ctx = canvas.getContext("2d");
  let state = { speech: "…", nodes: [], connections: [], ideas: [], capacity: 8, form: "humano" };
  function frame(now) {
    drawHouse(ctx, state, highlight, now || 0);
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
  async function pull() {
    try {
      state = await (await fetch("/v1/state")).json();
      paint(state);
    } catch (err) { /* hub down */ }
  }
    function paint(next) {
    const speech = document.getElementById("speech");
    if (speech) speech.textContent = next.speech || "…";
    const ideas = document.getElementById("ideas");
    if (ideas) {
      ideas.textContent = "";
      (next.ideas || []).slice().reverse().forEach((i) => {
        const li = document.createElement("li");
        li.textContent = (i.a || "") + " ↔ " + (i.b || "") + ": " + (i.text || "");
        ideas.appendChild(li);
      });
    }
    const cap = document.getElementById("capacity");
    if (cap) {
      const links = (next.connections || []).length;
      cap.textContent = "capacidad " + (next.capacity || 0) + (links ? " · " + links + " cruces" : "");
    }
    const peers = document.getElementById("peers");
    if (peers) {
      const mine = ((next.notebooks || {})[highlight] || []);
      const last = mine[mine.length - 1];
      peers.textContent = last
        ? "aprendió de " + last.from + ": " + last.text + " · capacidad " + (next.capacity || 0)
        : "";
    }
    const lif = document.getElementById("lif");
    if (lif && next.lif && next.lif.rates_per_ks) {
      lif.textContent = "LIF " + next.lif.engine + " tasas " + next.lif.rates_per_ks.join(", ");
    }
    const mem = document.getElementById("mem");
    if (mem) {
      mem.textContent = "";
      (next.memories || []).slice().reverse().slice(0, 6).forEach((m) => {
        const li = document.createElement("li");
        li.textContent = (m.source || "") + " · " + (m.learned || "");
        mem.appendChild(li);
      });
    }
  }
  pull();
  setInterval(pull, 1200);
  return async function send(kind, text, form) {
    const body = { source: highlight, kind, text: text || "", form: form || undefined };
    const res = await fetch("/v1/interact", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Nexo-Presence-Token": window.NEXO_PRESENCE_TOKEN || "",
      },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (data.state) {
      state = data.state;
      paint(state);
    }
  };
}
