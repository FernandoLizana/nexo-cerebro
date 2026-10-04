/**
 * Hogar de Nexo — observatorio autónomo (sin clics de acción).
 */
(function () {
  const viewport3d = document.getElementById("game-3d");
  const canvas = document.getElementById("game-canvas");

  function enableCanvas2dFallback() {
    if (!canvas || !viewport3d) return null;
    canvas.classList.remove("hidden-canvas");
    canvas.classList.add("canvas-fallback");
    return canvas.getContext("2d");
  }

  let use3d = false;
  if (viewport3d && window.NexoRenderer && typeof THREE !== "undefined") {
    use3d = !!window.NexoRenderer.init(viewport3d);
    if (use3d) {
      window.NexoRenderer.setPickHandler((hit) => {
        let hint = "Observando: " + (hit.label || hit.kind);
        const qLabel =
          (hit.qualities && window.NexoRenderer.formatQualitiesLabel(hit.qualities)) ||
          (hit.mesh && hit.mesh.userData && hit.mesh.userData.qualities
            ? window.NexoRenderer.formatQualitiesLabel(hit.mesh.userData.qualities)
            : "");
        if (qLabel) hint += " — " + qLabel;
        setHint(hint + " (Nexo actúa solo)");
      });
    }
  }
  const ctx = use3d ? null : enableCanvas2dFallback();
  if (!use3d && !ctx && canvas) {
    console.warn("Nexo: vista 3D no disponible; revisa conexión a Three.js CDN.");
  }

  const W = canvas ? canvas.width : 640;
  const H = canvas ? canvas.height : 400;
  const PHASE_LABEL = {
    dawn: "amanecer",
    day: "día",
    dusk: "atardecer",
    night: "noche",
  };
  const bubble = document.getElementById("bubble");
  const thoughtEl = document.getElementById("thought-bubble");
  const feelingsEl = document.getElementById("feelings-panel");
  const tvPanel = document.getElementById("tv-panel");
  const webPanel = document.getElementById("web-panel");
  const night = document.getElementById("night-overlay");
  const dreamOverlay = document.getElementById("dream-overlay");
  const objective = document.getElementById("objective");
  const hudMem = document.getElementById("hud-mem");
  const hudMood = document.getElementById("hud-mood");
  const hudEnergy = document.getElementById("hud-energy");
  const hudRoom = document.getElementById("hud-room");
  const hudBody = document.getElementById("hud-body");
  const hintEl = document.getElementById("interact-hint");

  const HOUSE_X = 168;
  const DEFAULT_FURNITURE = [
    { id: "door", kind: "door", x: 178, y: 175, w: 8, h: 70, label: "puerta" },
    { id: "desk", kind: "desk", x: 500, y: 55, w: 120, h: 55, label: "escritorio" },
    { id: "tv", kind: "tv", x: 340, y: 88, w: 90, h: 52, label: "televisión" },
    { id: "fridge", kind: "fridge", x: 230, y: 290, w: 55, h: 70, label: "nevera" },
    { id: "bed", kind: "bed", x: 520, y: 285, w: 95, h: 55, label: "cama" },
    { id: "sofa", kind: "sofa", x: 300, y: 220, w: 100, h: 45, label: "sofá" },
    { id: "bath", kind: "bath", x: 395, y: 288, w: 72, h: 58, label: "bañera" },
    { id: "toilet", kind: "toilet", x: 475, y: 292, w: 48, h: 52, label: "inodoro" },
  ];

  let world = {
    agent: { x: 120, y: 220, dir: 1 },
    objects: [],
    furniture: DEFAULT_FURNITURE.slice(),
    trees: [],
    tv: {},
    web: {},
    room: "jardín",
  };
  let player = { x: 120, y: 220, dir: 1, frame: 0, mood: "calm" };
  let companion = { x: 280, y: 230, dir: -1, mood: "calm", name: "Nira" };
  let offspring = null;
  let ticking = false;
  let env = { phase: "day", light_level: 1, clock: "12:00", season: "primavera", realtime: true, paused: false };
  let tickTimer = null;
  let tickChainActive = false;
  let timeDragging = false;
  const TICK_BASE_MS = 3200;
  let dreamMode = false;
  let dreamFragments = [];
  let dreamFrame = 0;

  function minuteToLabel(m) {
    const h = Math.floor(m / 60) % 24;
    const min = m % 60;
    return String(h).padStart(2, "0") + ":" + String(min).padStart(2, "0");
  }

  let turboActive = false;

  function syncTimelineFromEnv(e) {
    if (!e) return;
    const slider = document.getElementById("time-slider");
    const label = document.getElementById("time-slider-label");
    const mode = document.getElementById("timeline-mode");
    const feltHead = document.getElementById("timeline-nexo-felt");
    const playBtn = document.getElementById("btn-time-play");
    const scaleSel = document.getElementById("time-scale");
    const totalMin = (e.hour != null ? e.hour : 12) * 60 + (e.minute != null ? e.minute : 0);
    if (slider && !timeDragging) slider.value = String(totalMin);
    if (label) label.textContent = e.clock || minuteToLabel(totalMin);
    if (mode) {
      mode.textContent = e.realtime ? "hora real PC" : e.paused ? "sim · pausa" : "sim · " + (e.time_scale || 1) + "×";
    }
    if (playBtn) playBtn.textContent = e.paused ? "▶ Reanudar" : "⏸ Pausa";
    if (scaleSel && e.time_scale != null && !e.realtime) scaleSel.value = String(Math.round(e.time_scale));
    turboActive = !!(e.turbo || (e.learning_multiplier && e.learning_multiplier > 1.5));
    const turboBtn = document.getElementById("btn-time-turbo");
    if (turboBtn) {
      turboBtn.classList.toggle("turbo-on", turboActive);
      turboBtn.textContent = turboActive ? "⚡ Acelerando" : "⚡ Acelerar";
    }
    const tf = (e.temporal && e.temporal.felt) || "";
    if (feltHead && tf) feltHead.textContent = "Nexo: " + tf;
  }

  function renderTemporal(t) {
    const felt = document.getElementById("temporal-felt");
    const detail = document.getElementById("temporal-detail");
    if (!felt) return;
    if (!t) {
      felt.textContent = "—";
      if (detail) detail.textContent = "—";
      return;
    }
    felt.textContent = t.felt || "—";
    if (detail) {
      detail.textContent =
        (t.phase_label || t.phase || "") +
        " · " +
        (t.season || "") +
        " · " +
        (t.weekday || "") +
        (t.passage ? " · " + t.passage : "");
    }
  }

  async function postTime(body) {
    const j = await postJson("/api/time", body || {});
    if (j.environment) applyEnvironment(j.environment);
    if (j.temporal) renderTemporal(j.temporal);
    syncTimelineFromEnv({ ...(j.environment || {}), ...(j.clock || {}) });
    scheduleTicks();
    return j;
  }

  function scheduleTicks() {
    if (tickTimer) {
      clearInterval(tickTimer);
      tickTimer = null;
    }
    if (env.paused || tickChainActive) return;
    tickChainActive = true;
    const scale = env.realtime ? 1 : Math.max(0.25, env.time_scale || 1);
    const turboBoost = turboActive || env.turbo ? 3 : 1;

    (async function tickLoop() {
      while (!env.paused) {
        const ms = Math.max(800, TICK_BASE_MS / (scale * turboBoost));
        await new Promise((r) => setTimeout(r, ms));
        if (env.paused) break;
        await worldTick();
      }
      tickChainActive = false;
    })();
  }

  function bindTimeline() {
    const slider = document.getElementById("time-slider");
    const scaleSel = document.getElementById("time-scale");
    if (slider) {
      slider.addEventListener("input", () => {
        timeDragging = true;
        const m = parseInt(slider.value, 10);
        const lbl = document.getElementById("time-slider-label");
        if (lbl) lbl.textContent = minuteToLabel(m);
      });
      slider.addEventListener("change", async () => {
        const m = parseInt(slider.value, 10);
        timeDragging = false;
        await postTime({ realtime: false, hour: Math.floor(m / 60), minute: m % 60, paused: false });
      });
    }
    bindBtn("btn-time-realtime", () => postTime({ realtime: true, paused: false }));
    bindBtn("btn-time-play", () => postTime({ paused: !env.paused }));
    bindBtn("btn-time-back", () => postTime({ seek_minutes: -60, realtime: false }));
    bindBtn("btn-time-fwd", () => postTime({ seek_minutes: 60, realtime: false }));
    bindBtn("btn-time-turbo", () => {
      turboActive = !turboActive;
      return postTime({
        realtime: false,
        paused: false,
        turbo: turboActive,
        time_scale: turboActive ? 60 : 1,
        learning_multiplier: turboActive ? 6 : 1,
        minutes_per_tick: turboActive ? 18 : 7.2,
      });
    });
    if (scaleSel) {
      scaleSel.onchange = () => postTime({ time_scale: parseFloat(scaleSel.value), realtime: false, paused: false });
    }
  }

  function renderVirtualCortex(vc) {
    const el = document.getElementById("virtual-cortex-panel-body");
    if (!el) return;
    if (!vc) {
      el.innerHTML = "<p class='muted'>—</p>";
      return;
    }
    const disk = vc.disk || {};
    const gov = vc.decompress_governor || {};
    const recalled = vc.recalled_last || {};
    let html = `<p><span class="muted">Ensambles:</span> ${vc.assemblies ?? "—"} · `;
    html += `<span class="muted">virtuales:</span> ${vc.virtual_neurons ?? "—"} / ${vc.max_virtual_neurons ?? "—"}</p>`;
    html += `<p><span class="muted">Codec:</span> ${escapeHtml(disk.codec || "EGR1/EGRS")} · `;
    html += `${disk.per_assembly_bytes ?? "—"} B/ens · disco ${disk.used_pct ?? "—"}%</p>`;
    if (disk.legacy_npz_count > 0) {
      html += `<p class="muted">Migración: ${disk.legacy_npz_count} .npz legacy pendientes</p>`;
    }
    html += `<p><span class="muted">Descompresión tick:</span> ${gov.bytes_used ?? 0}/${gov.max_bytes_per_tick ?? "—"} B (${gov.bytes_pct ?? 0}%) · `;
    html += `ens ${gov.assemblies_used ?? 0}/${gov.max_assemblies ?? "—"} · chunks ${gov.chunks_used ?? 0}/${gov.max_chunks ?? "—"}`;
    if (gov.priority_boost > 0) html += ` · boost ${Math.round(gov.priority_boost * 100)}%`;
    html += `</p>`;
    if (recalled.recalled != null) {
      html += `<p class="muted">Último recall: ${recalled.recalled} ens · energía ${recalled.inject_energy ?? "—"}`;
      if (recalled.governor_blocked) html += " · <em>limitado por gobernador</em>";
      html += `</p>`;
    }
    if (gov.log && gov.log.length) {
      html += `<p class="muted">${gov.log.map(escapeHtml).join(" · ")}</p>`;
    }
    const pf = vc.decompression_prefetch || {};
    if (pf.plan && pf.plan.length) {
      html += `<p><span class="muted">Prefetch:</span> ${escapeHtml(pf.plan.join(" → "))}`;
      if (pf.total_warmed != null) html += ` · calentados ${pf.total_warmed}`;
      html += `</p>`;
    }
    if (gov.lifetime_ticks > 0) {
      html += `<p class="muted">Acumulado: ${Math.round((gov.lifetime_bytes || 0) / 1024)} KB descomp · `;
      html += `${Math.round((gov.lifetime_prefetch_bytes || 0) / 1024)} KB prefetch · ${gov.lifetime_ticks} ticks</p>`;
    }
    el.innerHTML = html;
  }

  function isFragmentarySpeech(text) {
    const t = (text || "").trim();
    if (!t) return true;
    if ((t.match(/…|\.\.\./g) || []).length >= 2) return true;
    if (/^….*…$/.test(t) && t.split(/\s+/).length <= 8) return true;
    if (/^\.\./.test(t) && (t.match(/\.\./g) || []).length >= 2) return true;
    return false;
  }

  function renderConsciousness(con) {
    const el = document.getElementById("consciousness-panel-body");
    if (!el) return;
    if (!con) {
      el.innerHTML = "<p class='muted'>Esperando primer tick del mundo…</p>";
      return;
    }
    const w = con.winner || {};
    const meta = con.metacognition || {};
    const self = con.self || {};
    const focus = w.label || (self.narrative && self.narrative[0]) || self.top_feeling || "";
    let html = `<p><span class="muted">Foco:</span> <strong>${escapeHtml(focus || "Atención difusa")}</strong>`;
    if (w.salience != null) html += ` <span class="muted">(${Math.round(w.salience * 100)}%)</span>`;
    html += `</p>`;
    html += `<p><span class="muted">Metacognición:</span> ${escapeHtml(meta.felt || "—")} · claridad ${Math.round((meta.clarity || 0) * 100)}% · duda ${Math.round((meta.doubt || 0) * 100)}%</p>`;
    if (self.narrative && self.narrative.length) {
      html += `<p class="muted">Yo: ${escapeHtml(self.narrative.slice(0, 3).join(" → "))}</p>`;
    }
    const others = (con.winners || []).slice(1, 3);
    if (others.length) {
      html += `<p class="muted">También presente: ${others.map((o) => escapeHtml(o.label)).join(" · ")}</p>`;
    }
    if (con.suppressed && con.suppressed.length) {
      html += `<p class="muted">Inconsciente (filtrado): ${con.suppressed.slice(0, 3).map(escapeHtml).join(", ")}</p>`;
    }
    if (con.log && con.log.length) {
      html += `<ul class="muted">${con.log.map((l) => `<li>${escapeHtml(l)}</li>`).join("")}</ul>`;
    }
    el.innerHTML = html;
  }

  function renderHedonics(hed) {
    const el = document.getElementById("hedonics-panel-body");
    if (!el) return;
    if (!hed) {
      el.innerHTML = "<p class='muted'>Esperando datos del cuerpo…</p>";
      return;
    }
    const rows = [
      ["placer", hed.pleasure],
      ["satisfacción", hed.satisfaction],
      ["antojo", hed.craving],
      ["saciedad", hed.satiety],
      ["μ-opioide", hed.mu_opioid],
      ["endocannabinoide", hed.endocannabinoid],
      ["cansancio sentido", hed.fatigue_felt],
    ];
    let html = rows
      .map(
        ([name, v]) =>
          `<div class="feel-row"><span>${escapeHtml(name)}</span><div class="bar"><i style="width:${Math.round((v || 0) * 100)}%"></i></div><span>${Math.round((v || 0) * 100)}%</span></div>`
      )
      .join("");
    if (hed.last_reward) {
      html += `<p class="muted">Última recompensa: ${escapeHtml(hed.last_reward)}</p>`;
    }
    if (hed.log && hed.log.length) {
      html += `<ul class="muted">${hed.log.map((l) => `<li>${escapeHtml(l)}</li>`).join("")}</ul>`;
    }
    el.innerHTML = html;
  }

  function renderPantry(world) {
    const el = document.getElementById("pantry-panel-body");
    if (!el) return;
    const pantry = (world && world.pantry) || [];
    const crops = ((world && world.objects) || []).filter((o) => o.kind === "crop");
    const ripe = crops.filter((c) => !c.meta || c.meta.ripe !== false);
    let html = `<p><span class="muted">Cultivos maduros:</span> ${ripe.length} / ${crops.length}</p>`;
    if (Array.isArray(pantry)) {
      if (!pantry.length) {
        html += "<p class='muted'>Despensa vacía</p>";
      } else {
        html +=
          "<ul>" +
          pantry.map((p) => `<li>${escapeHtml(p.label || p.food || "?")}${p.raw ? " (crudo)" : " (cocido)"}</li>`).join("") +
          "</ul>";
      }
    } else {
      const items = pantry.items || [];
      html += `<p><span class="muted">Crudo:</span> ${pantry.raw_count || 0} · <span class="muted">Cocido:</span> ${pantry.cooked_count || 0}</p>`;
      if (items.length) {
        html +=
          "<ul>" +
          items.map((p) => `<li>${escapeHtml(p.label || p.food || "?")}${p.raw ? " (crudo)" : " (cocido)"}</li>`).join("") +
          "</ul>";
      } else {
        html += "<p class='muted'>Despensa vacía</p>";
      }
    }
    el.innerHTML = html;
  }

  function renderBiomechanics(bio) {
    const el = document.getElementById("biomech-panel-body");
    if (!el) return;
    if (!bio) {
      el.innerHTML = "<p class='muted'>Esperando simulación física…</p>";
      return;
    }
    const joints = bio.joints || {};
    const topJoint = Object.entries(joints).sort((a, b) => b[1] - a[1])[0];
    const shock = bio.spine_shock || (bio.bones && bio.bones.spine_shock) || [];
    const shockMax = shock.length ? Math.max.apply(null, shock) : 0;
    el.innerHTML =
      `<p><span class="muted">Marcha:</span> ${escapeHtml(bio.gait || "—")} · ${Math.round(bio.speed || 0)} px/s</p>` +
      `<p><span class="muted">Equilibrio:</span> ${Math.round((bio.equilibrium || 0) * 100)}%` +
      (bio.ragdoll ? " · <strong>ragdoll</strong>" : "") +
      `</p>` +
      (bio.in_water
        ? `<p><span class="muted">Agua:</span> ${Math.round((bio.water_depth || 0) * 100)}% sumergido · flotabilidad ${Math.round(bio.buoyancy_N || 0)} N</p>`
        : "") +
      (shockMax > 0.08
        ? `<p><span class="muted">Onda espinal:</span> ${Math.round(shockMax * 100)}% (sacral→cervical)</p>`
        : "") +
      `<p><span class="muted">Cardio:</span> ❤ ${Math.round(bio.heart_rate_bpm || 0)} · resp ${Math.round(bio.breath_rate || 0)}/min · flujo ${Math.round((bio.blood_flow || 0) * 100)}%</p>` +
      `<p><span class="muted">Fatiga física:</span> ${Math.round((bio.physical_fatigue || 0) * 100)}%</p>` +
      (topJoint && topJoint[1] > 0.1
        ? `<p class="muted">Articulación más cargada: ${escapeHtml(topJoint[0])} ${Math.round(topJoint[1] * 100)}%</p>`
        : "");
  }

  function renderPain(body) {
    const el = document.getElementById("pain-map");
    if (!el) return;
    const pain = (body && body.pain) || {};
    const noc = (body && body.nociception) || {};
    const regions = [
      ["cabeza", pain.head || 0],
      ["torso", pain.torso || 0],
      ["extremidades", pain.limbs || 0],
      ["malestar", pain.ache || 0],
    ];
    let html = regions
      .map(
        ([name, v]) =>
          `<div class="pain-bar"><span>${name}</span><i style="--pct:${Math.round(v * 100)}%"></i><span>${Math.round(v * 100)}%</span></div>`
      )
      .join("");
    if (noc.a_delta || noc.c_fiber) {
      const ad = noc.a_delta || {};
      const cf = noc.c_fiber || {};
      const dh = noc.dorsal_horn || {};
      html += `<p class="muted anatomy-subtitle">Terminal Aδ/C → asta dorsal</p>`;
      html += `<div class="pain-bar"><span>Aδ (rápido)</span><i style="--pct:${Math.round(((ad.limbs || 0) + (ad.head || 0) + (ad.torso || 0)) / 3 * 100)}%"></i></div>`;
      html += `<div class="pain-bar"><span>C (lento)</span><i style="--pct:${Math.round(((cf.limbs || 0) + (cf.torso || 0) + (cf.viscera || 0)) / 3 * 100)}%"></i></div>`;
      html += `<p class="muted">Relé tálamo ${Math.round((noc.thalamic_relay || 0) * 100)}% · sensibilización ${Math.round((noc.central_sensitization || 0) * 100)}%</p>`;
      if (noc.last_stimuli && noc.last_stimuli.length) {
        html += `<p class="muted">${escapeHtml(noc.last_stimuli[0].label || noc.last_stimuli[0].modality || "")}</p>`;
      }
    }
    el.innerHTML = html;
  }

  function renderVision(vision) {
    const gistEl = document.getElementById("vision-gist");
    const listEl = document.getElementById("vision-percepts");
    if (!gistEl) return;
    if (!vision) {
      gistEl.textContent = "—";
      if (listEl) listEl.innerHTML = "";
      return;
    }
    gistEl.textContent = vision.scene_gist || "—";
    if (listEl) {
      const items = (vision.foveal || []).concat(vision.peripheral || []).slice(0, 5);
      listEl.innerHTML = items.length
        ? items.map((p) => `<li>${escapeHtml(p.interpretation || p.label || p.kind)}</li>`).join("")
        : "<li class='muted'>Nada en el campo visual</li>";
    }
  }

  function renderThoughtFlow(data) {
    const el = document.getElementById("thought-flow");
    if (!el) return;
    const flow = data.thought_flow || (data.thought && data.thought.flow) || [];
    if (!flow.length) {
      const txt = data.thought && data.thought.text;
      el.textContent = txt && !String(txt).startsWith("{") ? txt : "…";
      return;
    }
    el.innerHTML = flow
      .map((f) => `<span class="flow-frag kind-${f.kind || "misc"}">${escapeHtml(f.raw || "…")}</span>`)
      .join(" <span class='flow-sep'>·</span> ");
  }

  function canvasPoint(e) {
    const target = use3d && window.NexoRenderer.domElement()
      ? window.NexoRenderer.domElement()
      : canvas;
    if (!target) return { x: 0, y: 0 };
    const rect = target.getBoundingClientRect();
    return {
      x: (640 / rect.width) * (e.clientX - rect.left),
      y: (400 / rect.height) * (e.clientY - rect.top),
    };
  }

  function applyEnvironment(w) {
    const e = { ...((w && w.environment) || w || {}), ...((w && w.clock) || {}) };
    if (!e || !e.phase) return;
    env = e;
    syncTimelineFromEnv(e);
    if (e.temporal) renderTemporal(e.temporal);
    const clockEl = document.getElementById("env-clock");
    const phaseEl = document.getElementById("env-phase");
    const seasonEl = document.getElementById("env-season");
    const zoneEl = document.getElementById("env-zone");
    if (clockEl) clockEl.textContent = e.clock || "—";
    if (phaseEl) phaseEl.textContent = e.phase_label || PHASE_LABEL[e.phase] || e.phase || "—";
    if (seasonEl) seasonEl.textContent = e.season || "—";
    const hz = (w && w.hero_zone) || e.hero_zone;
    if (zoneEl) zoneEl.textContent = hz ? hz.name : "—";
    if (night && !dreamMode) {
      const dark = 1 - (e.light_level != null ? e.light_level : 1);
      night.style.opacity = dark > 0.08 ? String(Math.min(0.82, dark * 0.95)) : "0";
      night.classList.toggle("show", dark > 0.08);
    }
  }

  function skyColor() {
    const p = env.phase || "day";
    if (p === "night") return "#0a1628";
    if (p === "dusk") return "#4a3728";
    if (p === "dawn") return "#6a8caf";
    return "#87ceeb";
  }

  function gardenGrass() {
    const s = env.season || "primavera";
    if (s === "otoño") return ["#6b5a2e", "#7a6838"];
    if (s === "invierno") return ["#3d5a40", "#4a6b4e"];
    if (s === "verano") return ["#3d7a32", "#4a9c38"];
    return ["#4a8538", "#5a9c45"];
  }

  function drawGarden() {
    ctx.fillStyle = skyColor();
    ctx.fillRect(0, 0, HOUSE_X, 55);
    if (env.phase === "night") {
      ctx.fillStyle = "rgba(255,255,220,0.85)";
      for (let i = 0; i < 12; i++) {
        const sx = 18 + (i * 37) % (HOUSE_X - 20);
        const sy = 8 + (i * 13) % 28;
        ctx.beginPath();
        ctx.arc(sx, sy, i % 3 === 0 ? 1.2 : 0.7, 0, Math.PI * 2);
        ctx.fill();
      }
    }
    const grass = gardenGrass();
    for (let y = 55; y < H; y += 16) {
      for (let x = 0; x < HOUSE_X; x += 16) {
        ctx.fillStyle = (x + y) % 32 === 0 ? grass[0] : grass[1];
        ctx.fillRect(x, y, 16, 16);
      }
    }
    ctx.fillStyle = "#fff";
    ctx.font = "bold 11px sans-serif";
    const hz = world.hero_zone || env.hero_zone;
    ctx.fillText("JARDÍN" + (hz && hz.key === "threshold" ? " · umbral" : ""), 12, 20);
    (world.trees || []).forEach((t) => {
      ctx.fillStyle = "#2d5a27";
      ctx.beginPath();
      ctx.arc(t.x, t.y, t.r, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "#1e4620";
      ctx.fillRect(t.x - 4, t.y, 8, t.r);
    });
  }

  function drawHouseShell() {
    const hw = W - HOUSE_X;
    ctx.fillStyle = "#5d4037";
    ctx.fillRect(HOUSE_X - 4, 0, hw + 8, H);
    ctx.fillStyle = "#8d6e63";
    ctx.beginPath();
    ctx.moveTo(HOUSE_X - 8, 48);
    ctx.lineTo(HOUSE_X + hw / 2, 8);
    ctx.lineTo(W + 4, 48);
    ctx.closePath();
    ctx.fill();
    ctx.fillStyle = "#ffe0b2";
    for (let y = 48; y < H; y += 18) {
      ctx.fillStyle = y % 36 === 0 ? "#ffcc80" : "#ffe0b2";
      ctx.fillRect(HOUSE_X, y, hw, 9);
    }
    ctx.fillStyle = "#fff";
    ctx.font = "bold 12px sans-serif";
    ctx.fillText("CASA DE NEXO", HOUSE_X + 14, 38);
    ctx.strokeStyle = "#5d4037";
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(HOUSE_X, 48);
    ctx.lineTo(HOUSE_X, H);
    ctx.stroke();
  }

  function drawFurniture(fu) {
    const colors = {
      desk: "#6d4c33",
      tv: "#263238",
      fridge: "#eceff1",
      bed: "#7986cb",
      sofa: "#a1887f",
      door: "#4e342e",
      bath: "#81d4fa",
      toilet: "#e0e0e0",
    };
    ctx.fillStyle = colors[fu.kind] || "#888";
    ctx.fillRect(fu.x, fu.y, fu.w, fu.h);
    ctx.strokeStyle = "#222";
    ctx.lineWidth = 1;
    ctx.strokeRect(fu.x, fu.y, fu.w, fu.h);

    if (fu.kind === "tv") {
      ctx.fillStyle = world.tv && world.tv.active ? "#1565c0" : "#000";
      ctx.fillRect(fu.x + 6, fu.y + 6, fu.w - 12, fu.h - 14);
      ctx.fillStyle = "#fff";
      ctx.font = "9px sans-serif";
      ctx.fillText("TV", fu.x + fu.w / 2 - 8, fu.y + fu.h / 2);
    }
    if (fu.kind === "desk") {
      ctx.fillStyle = "#3e2723";
      ctx.fillRect(fu.x, fu.y + fu.h - 8, fu.w, 8);
      ctx.fillStyle = world.web && world.web.active ? "#1e88e5" : "#222";
      ctx.fillRect(fu.x + fu.w * 0.55, fu.y + 4, fu.w * 0.38, fu.h * 0.45);
      ctx.fillStyle = "#fff";
      ctx.font = "8px sans-serif";
      ctx.fillText("escritorio", fu.x + 4, fu.y - 4);
    }
    ctx.fillStyle = "#333";
    ctx.font = "8px sans-serif";
    if (fu.kind !== "desk") ctx.fillText(fu.label || fu.kind, fu.x + 2, fu.y - 3);
  }

  function drawObject(obj) {
    ctx.save();
    ctx.translate(obj.x, obj.y);
    if (obj.kind === "book") {
      // Read alias: saved objects used meta.tarot.
      const isArchetypeCard = !!(obj.meta && (obj.meta.archetype_card || obj.meta.tarot));
      ctx.fillStyle = isArchetypeCard ? "#6a1b9a" : "#1565c0";
      ctx.fillRect(-10, -12, 20, 24);
      ctx.fillStyle = "#fff";
      ctx.font = "10px serif";
      ctx.textAlign = "center";
      ctx.fillText(isArchetypeCard ? "◈" : "📖", 0, 4);
    } else {
      ctx.fillStyle = "#e74c3c";
      ctx.fillRect(-12, -12, 24, 24);
    }
    ctx.restore();
  }

  function drawNexo(p) {
    drawApe(p, "Nexo", "#f4d03f", "#f9e076");
  }

  function drawCompanion(p) {
    drawApe(p, p.name || "Nira", "#e1bee7", "#f3e5f5", "#8e24aa");
  }

  function drawOffspring(p) {
    drawApe(p, p.name || "Hijo", "#ffcc80", "#ffe0b2", "#ef6c00", 0.75);
  }

  function drawApe(p, label, fur, belly, earColor, scale) {
    scale = scale || 1;
    const bounce = Math.sin(p.frame * 0.15) * 2;
    ctx.save();
    ctx.translate(p.x, p.y + bounce);
    ctx.scale(scale, scale);
    if (p.dir < 0) ctx.scale(-1, 1);
    ctx.fillStyle = fur;
    ctx.fillRect(-14, -8, 28, 22);
    ctx.fillStyle = belly;
    ctx.fillRect(-10, -4, 20, 14);
    ctx.fillStyle = earColor || fur;
    ctx.fillRect(-16, -18, 10, 12);
    ctx.fillRect(6, -18, 10, 12);
    ctx.fillStyle = "#222";
    ctx.fillRect(-8, -6, 5, 6);
    ctx.fillRect(3, -6, 5, 6);
    ctx.restore();
    ctx.fillStyle = earColor || "#e94560";
    ctx.font = "9px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(label, p.x, p.y - 28 + bounce);
  }

  function showVerbalDialogue(sd) {
    if (!sd || !sd.nexo) return;
    if (window.caregiverSensors && window.caregiverSensors.isActive && window.caregiverSensors.isActive()) {
      return;
    }
    showBubble("Nexo: " + sd.nexo, 5500);
    clearTimeout(showVerbalDialogue._t2);
    showVerbalDialogue._t2 = setTimeout(() => {
      if (sd.nira) showBubble("Nira: " + sd.nira, 5500);
    }, 5800);
  }

  function showBubble(text, ms = 6000) {
    if (!text || text === "…") return;
    if (bubble) {
      bubble.textContent = text;
      bubble.classList.remove("hidden");
      bubble.classList.add("show");
    }
    clearTimeout(showBubble._t);
    showBubble._t = setTimeout(() => bubble.classList.remove("show"), ms);
  }

  function showThought(thought) {
    if (!thought) return;
    const flowEl = document.getElementById("thought-flow");
    const text = thought.text && !String(thought.text).startsWith("{") ? thought.text : null;
    if (flowEl && thought.flow && thought.flow.length) {
      renderThoughtFlow({ thought_flow: thought.flow, thought });
    } else if (text && thoughtEl) {
      thoughtEl.textContent = "💭 " + text;
      thoughtEl.classList.add("show");
      clearTimeout(showThought._t);
      showThought._t = setTimeout(() => thoughtEl.classList.remove("show"), 8000);
    }
  }

  function setHint(t) {
    if (hintEl) hintEl.textContent = t;
  }

  function renderFeelings(data) {
    const body = data.body || {};
    const feelings = body.feelings || [];
    const text = data.feelings_text || "";
    const aff = data.affect || {};
    let html = "";
    if (aff.felt) {
      html += `<p class="feel-chemical">⚗️ ${escapeHtml(aff.felt)} <span class="muted">(química)</span></p>`;
    }
    if (text) html += `<p class="feel-narrative">${escapeHtml(text)}</p>`;
    html += '<div class="feel-bars">';
    feelings.forEach((f) => {
      const pct = Math.round(f.intensity * 100);
      html += `<div class="feel-row"><span>${f.signal}</span><div class="bar"><i style="width:${pct}%"></i></div><span>${pct}%</span></div>`;
    });
    html += "</div>";
    if (feelingsEl) feelingsEl.innerHTML = html || "<p class='muted'>Sensaciones neutras…</p>";
    if (tvPanel && world.tv && world.tv.active && world.tv.url) {
      tvPanel.innerHTML = `<p>📺 Nexo eligió: <strong>${escapeHtml(world.tv.title || world.tv.query)}</strong></p>
        <a href="${escapeHtml(world.tv.url)}" target="_blank" rel="noopener">Abrir en YouTube ↗</a>`;
      tvPanel.classList.add("show");
    } else if (tvPanel) tvPanel.classList.remove("show");
    if (webPanel && world.web && world.web.active && world.web.results && world.web.results.length) {
      const prov = world.web.provider || "web";
      let links = world.web.results
        .slice(0, 4)
        .map(
          (r) =>
            `<li><a href="${escapeHtml(r.url)}" target="_blank" rel="noopener">${escapeHtml(r.title || r.url)}</a>` +
            (r.snippet ? `<span class="web-snippet">${escapeHtml(r.snippet.slice(0, 90))}</span>` : "") +
            `</li>`
        )
        .join("");
      webPanel.innerHTML = `<p>🔍 Nexo buscó: <strong>${escapeHtml(world.web.query)}</strong> <span class="muted">(${escapeHtml(prov)})</span></p>
        <ul class="web-results">${links}</ul>`;
      webPanel.classList.add("show");
    } else if (webPanel) webPanel.classList.remove("show");
  }

  function escapeHtml(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
  }

  function renderActivity(data) {
    const evs = data.world_events || [];
    const last = evs.length ? evs[evs.length - 1] : null;
    const delib = data.deliberation || (data.cognition && data.cognition.decision);
    const parts = [];
    if (delib && delib.choice) parts.push(delib.choice);
    if (last) {
      if (last.type === "move") parts.push("camina");
      else if (last.type === "tv_use") parts.push("mira TV");
      else if (last.type === "web_search") parts.push("busca en web");
      else if (last.type === "read") parts.push("lee");
      else if (last.type === "eat") parts.push("come");
      else if (last.type === "eat_cooked") parts.push("come cocido");
      else if (last.type === "harvest") parts.push("cosecha");
      else if (last.type === "cook") parts.push("cocina");
      else if (last.type === "rest") parts.push("descansa");
      else if (last.type === "bump") parts.push("golpe en " + (last.target || "mueble"));
      else if (last.type) parts.push(last.type);
    }
    if (data.world && data.world.agent) {
      const ag = data.world.agent;
      parts.push("@" + Math.round(ag.x) + "," + Math.round(ag.y));
    }
    if (parts.length) setHint("Nexo: " + parts.join(" · "));
  }

  function applyWorld(w) {
    if (!w) return;
    world = w;
    if (!world.furniture || !world.furniture.length) {
      world.furniture = DEFAULT_FURNITURE.slice();
    }
    if (w.tv) world.tv = w.tv;
    if (w.web) world.web = w.web;
    if (w.environment) applyEnvironment(w);
    else if (w.hero_zone) world.hero_zone = w.hero_zone;
    const ag = w.agent || { x: 120, y: 220, dir: 1 };
    player.x = ag.x ?? 120;
    player.y = ag.y ?? 220;
    player.dir = ag.dir ?? 1;
    player.gait_phase = ag.gait_phase ?? 0;
    player.walking = !!ag.walking;
    if (w.biomechanics) {
      player.biomech = w.biomechanics;
      if (w.biomechanics.gait_phase != null) player.gait_phase = w.biomechanics.gait_phase;
    }
    if (w.companion) {
      companion.x = w.companion.x;
      companion.y = w.companion.y;
      companion.dir = w.companion.dir || -1;
      companion.gait_phase = w.companion.gait_phase ?? 0;
      companion.walking = !!w.companion.walking;
      companion.name = w.companion.name || "Nira";
      companion.mood = (w.companion.persona && w.companion.persona.mood) || "calm";
    }
    if (w.offspring) {
      offspring = offspring || { frame: 0 };
      offspring.x = w.offspring.x;
      offspring.y = w.offspring.y;
      offspring.dir = w.offspring.dir || 1;
      offspring.name = w.offspring.name || "Hijo";
    } else {
      offspring = null;
    }
    updateMetaPanels(w);
    if (w.dream_mode && w.dreams) startDreamMode(w.dreams);
    if (w.vision) renderVision(w.vision);
  }

  function startDreamMode(fragments) {
    dreamMode = true;
    dreamFragments = fragments || [];
    dreamFrame = 0;
    if (dreamOverlay) {
      dreamOverlay.classList.remove("hidden");
      dreamOverlay.innerHTML = "<span class='dream-title'>💤 sueño REM</span>";
    }
    if (night) {
      night.classList.add("show", "dream");
      night.style.opacity = "0.88";
    }
  }

  function stopDreamMode(ms) {
    setTimeout(() => {
      dreamMode = false;
      dreamFragments = [];
      if (dreamOverlay) {
        dreamOverlay.classList.add("hidden");
        dreamOverlay.innerHTML = "";
      }
      if (night) {
        night.classList.remove("dream");
        applyEnvironment(world);
      }
    }, ms || 8000);
  }

  function drawDreams() {
    if (!dreamMode || !dreamFragments.length) return;
    dreamFrame++;
    dreamFragments.forEach((d, i) => {
      const t = dreamFrame * 0.02 + i;
      const x = d.x + Math.sin(t) * 18 * (d.drift || 0.5);
      const y = d.y + Math.cos(t * 0.7) * 12;
      ctx.save();
      ctx.globalAlpha = (d.alpha || 0.6) * (0.7 + 0.3 * Math.sin(t));
      ctx.fillStyle = `hsl(${d.hue || 270}, 55%, 72%)`;
      ctx.font = "italic 11px Georgia, serif";
      ctx.textAlign = "center";
      ctx.fillText(d.text, x, y);
      ctx.restore();
    });
  }

  function updateMetaPanels(w) {
    const lc = w.lifecycle || {};
    const j = w.journey || {};
    const ageEl = document.getElementById("lc-age");
    const vitEl = document.getElementById("lc-vit");
    const stageEl = document.getElementById("lc-stage");
    const jStage = document.getElementById("journey-stage");
    const jOrdeal = document.getElementById("journey-ordeal");
    const rebornBtn = document.getElementById("btn-reborn");
    if (ageEl) ageEl.textContent = lc.age_years != null ? lc.age_years + " años" : "—";
    if (vitEl) vitEl.textContent = lc.vitality != null ? Math.round(lc.vitality * 100) + "%" : "—";
    if (stageEl) stageEl.textContent = lc.stage || "—";
    if (jStage && j.stage) jStage.textContent = j.stage.name || j.stage.key || "—";
    if (jOrdeal) {
      jOrdeal.textContent = j.active_ordeal ? "⚔ " + j.active_ordeal.label : "";
    }
    if (rebornBtn) {
      rebornBtn.classList.toggle("hidden", lc.alive !== false);
    }
    const chem = w.chemistry || {};
    const bondAttr = document.getElementById("bond-attr");
    const bondOxy = document.getElementById("bond-oxy");
    if (bondAttr) bondAttr.textContent = chem.attraction != null ? Math.round(chem.attraction * 100) + "%" : "—";
    if (bondOxy) bondOxy.textContent = chem.nexo_oxytocin != null ? Math.round(chem.nexo_oxytocin * 100) + "%" : "—";
  }

  function updateHud(data) {
    if (!data) return;
    const c = data.character || {};
    const h = data.hypothalamus || {};
    const body = data.body || {};
    hudMem.textContent = data.hippocampus_size ?? "—";
    hudMood.textContent = c.mood || h.mood || "—";
    const energy = c.energy != null ? c.energy : h.energy;
    hudEnergy.textContent = energy != null ? Math.round(energy * 100) + "%" : "—";
    if (hudRoom) hudRoom.textContent = (data.world && data.world.room) || world.room || "—";
    if (hudBody) {
      const top = (body.feelings || [])[0];
      hudBody.textContent = top ? top.signal + " " + Math.round(top.intensity * 100) + "%" : "—";
    }
    player.mood = c.mood || "calm";
    renderThoughtFlow(data);
    renderFeelings(data);
    renderPain(data.body);
    renderBiomechanics(data.biomechanics || (data.world && data.world.biomechanics));
    renderConsciousness(data.consciousness || (data.cognition && data.cognition.consciousness));
    renderVirtualCortex(data.virtual_cortex);
    renderHedonics(data.hedonics);
    renderPantry(data.world);
    renderVision(data.vision || (data.world && data.world.vision));
    renderDrives(data.drives || (data.body && data.body.drives));
    // Read alias: older payloads stored card stats on "tarot".
    renderArchetypeCardStats(
      data.archetype_cards ||
        (data.world && data.world.archetype_cards) ||
        data.tarot ||
        (data.world && data.world.tarot)
    );
    renderAutonomy(data.autonomy_log);
    renderCognition(data.cognition);
    renderCausalHud(data.causal_hud || data);
    renderObservatory(data.observatory_hud || {});
    renderImagination(data.imagination);
    renderAffect(data.affect);
    renderAnatomy(data.neuroanatomy);
    renderLobes(data.lobes, data.lobe_cortex);
    renderTemporal(data.temporal);
    renderDialogue(data);
    renderLearning(data.learning_log);
    renderSleepStudy(data.sleep_study, data);
    renderCurriculum(data.curriculum);
    renderStudyTrack(data.clinical_neurology, "clinical");
    renderStudyTrack(data.biopsych, "biopsych", true);
    renderStudyTrack(data.infant_brain, "infant-brain");
    renderBrainFacts(data.brain_facts, data.circuits);
    renderAnatomyBook(data.anatomy_book);
    renderTypedMemory(data.typed_memory, data.sleep_architecture);
    renderActivity(data);
    if (data.social_dialogue && data.social_dialogue.verbal) {
      showVerbalDialogue(data.social_dialogue);
    }
    const caregiverOn =
      window.caregiverSensors && window.caregiverSensors.isActive && window.caregiverSensors.isActive();
    if (data.companion && data.companion.persona && data.companion.persona.message && !caregiverOn) {
      const nx = data.character && data.character.message ? data.character.message : "";
      const nr = data.companion.persona.message;
      const sd = data.social_dialogue || {};
      const nxLine = sd.nexo && !isFragmentarySpeech(sd.nexo) ? sd.nexo : nx;
      const nrLine = sd.nira && !isFragmentarySpeech(sd.nira) ? sd.nira : nr;
      if (sd.nexo && !isFragmentarySpeech(sd.nexo)) {
        setHint("Nexo: " + nxLine + " · Nira: " + (nrLine || "…"));
      } else if (nxLine && !isFragmentarySpeech(nxLine) && nrLine && !isFragmentarySpeech(nrLine)) {
        setHint("Nexo: " + nxLine + " · Nira: " + nrLine);
      } else if (nrLine && !isFragmentarySpeech(nrLine)) {
        setHint("Nira: " + nrLine);
      }
    }
    if (data.world) applyWorld(data.world);
    if (data.biomechanics) player.biomech = data.biomechanics;
    else if (data.environment) applyEnvironment(data.environment);
    else if (data.lifecycle || data.journey) updateMetaPanels(data);
    else if (data.companion) applyWorld({ ...world, companion: data.companion });
    if (data.environment && data.world) applyEnvironment(data.environment);
    if (data.temporal) {
      renderTemporal(data.temporal);
      const feltHead = document.getElementById("timeline-nexo-felt");
      if (feltHead && data.temporal.felt) feltHead.textContent = "Nexo: " + data.temporal.felt;
    }
    if (data.environment && (data.environment.paused != null || data.environment.realtime != null)) {
      env = { ...env, ...data.environment };
      scheduleTicks();
    }
  }

  async function postJson(url, body) {
    const r = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
    });
    const j = await r.json();
    if (!r.ok) throw new Error(j.error || r.statusText);
    return j;
  }

  let imaginationLayer = 0;

  async function refreshImaginationFrame() {
    try {
      const r = await fetch("/api/imagination/frame");
      if (!r.ok) return;
      const im = await r.json();
      renderImagination(im);
    } catch (_) {
      /* ignore */
    }
  }

  function renderImagination(im) {
    const cap = document.getElementById("imagination-caption");
    const srcEl = document.getElementById("imagination-source");
    const imgA = document.getElementById("imagination-img-a");
    const imgB = document.getElementById("imagination-img-b");
    const frame = document.querySelector(".imagination-frame");
    if (!cap || !imgA || !imgB) return;
    if (!im || !im.image_b64) {
      if (frame) frame.classList.add("stream-waiting");
      return;
    }
    if (frame) frame.classList.remove("stream-waiting");

    cap.textContent = im.caption || im.label || "—";
    if (srcEl) {
      const parts = [];
      if (im.sources && im.sources.length) parts.push(im.sources.join(" · "));
      if (im.modality) parts.push(im.modality);
      if (im.involuntary) parts.push("intrusión espontánea");
      srcEl.textContent = parts.length ? parts.join(" — ") : "default mode";
    }

    const url = "data:image/png;base64," + im.image_b64;
    imaginationLayer = 1 - imaginationLayer;
    const front = imaginationLayer ? imgB : imgA;
    const back = imaginationLayer ? imgA : imgB;
    front.onload = () => {
      front.classList.remove("hidden");
      front.classList.add("stream-front");
      front.classList.remove("stream-back");
      back.classList.add("stream-back");
      back.classList.remove("stream-front");
    };
    front.onerror = () => refreshImaginationFrame();
    front.src = url;
    back.classList.remove("hidden");
  }

  const AFFECT_LABELS = {
    dopamine: "Dopamina",
    serotonin: "Serotonina",
    norepinephrine: "Noradrenalina",
    acetylcholine: "Acetilcolina",
    gaba: "GABA",
    glutamate: "Glutamato",
    oxytocin: "Oxitocina",
    cortisol: "Cortisol",
  };

  function renderLobes(lobes, lobeCortex) {
    const el = document.getElementById("anatomy-lobes");
    if (!el) return;
    const act = (lobes && lobes.activity) || {};
    const cols = (lobeCortex && lobeCortex.columns) || (lobes && lobes.columns) || {};
    const olf = (lobes && lobes.olfaction) || {};
    const keys = ["occipital", "temporal", "parietal", "frontal", "olfactory"];
    const labels = {
      occipital: "Occipital",
      temporal: "Temporal",
      parietal: "Parietal",
      frontal: "Frontal",
      olfactory: "Olfato (directo)",
    };
    let html = keys
      .filter((k) => k !== "olfactory" || act[k])
      .map((k) => {
        const routePct = Math.round((act[k] || 0) * 100);
        const colPct = Math.round((cols[k] || 0) * 100);
        const colHint = cols[k] != null && cols[k] !== undefined ? ` · col ${colPct}%` : "";
        return (
          `<div class="anatomy-row"><span>${labels[k]}</span>` +
          `<div class="bar"><i style="width:${routePct}%"></i></div>` +
          `<span>${routePct}%${colHint}</span></div>`
        );
      })
      .join("");
    if (olf.label) {
      html += `<p class="muted anatomy-calloso">Olfato: ${escapeHtml(olf.label)} (${Math.round((olf.intensity || 0) * 100)}%)</p>`;
    }
    el.innerHTML = html;
  }

  function renderAnatomy(na) {
    const ANATOMY_GROUPS = {
      hemispheres: "Hemisferios",
      lobes: "Lóbulos",
      limbic: "Sistema límbico",
      subcortex: "Subcorteza",
      brainstem: "Tronco encefálico",
      language: "Lenguaje",
      tissue: "Tejido cerebral",
      support: "Protección y soporte",
      networks: "Redes cerebrales",
      peripheral: "Periferia y cuerpo",
    };
    const orchestra = document.getElementById("anatomy-orchestra");
    const hemi = document.getElementById("anatomy-hemispheres");
    const grid = document.getElementById("anatomy-structures");
    const nt = document.getElementById("anatomy-transmitters");
    if (!grid) return;
    if (!na || !na.structures) {
      if (orchestra) orchestra.textContent = "—";
      return;
    }
    const lines = na.orchestra || [];
    if (orchestra) {
      orchestra.innerHTML = lines.length
        ? lines.map((l) => `<span class="anatomy-line">${escapeHtml(l)}</span>`).join(" · ")
        : "—";
    }
    const h = na.hemispheres || {};
    if (hemi) {
      hemi.innerHTML =
        `<div class="anatomy-hemi-row"><span>Izquierdo</span>` +
        `<div class="bar"><i style="width:${Math.round((h.left || 0) * 100)}%"></i></div>` +
        `<span>${Math.round((h.left || 0) * 100)}%</span></div>` +
        `<div class="anatomy-hemi-row"><span>Derecho</span>` +
        `<div class="bar"><i style="width:${Math.round((h.right || 0) * 100)}%"></i></div>` +
        `<span>${Math.round((h.right || 0) * 100)}%</span></div>` +
        `<p class="muted anatomy-calloso">Calloso: transfer ${Math.round((h.corpus_callosum || 0) * 100)}% · asimetría ${Math.round((h.asymmetry || 0) * 100)}%</p>`;
    }
    const byGroup = {};
    (na.structures || []).forEach((s) => {
      const g = s.group || "other";
      if (!byGroup[g]) byGroup[g] = [];
      byGroup[g].push(s);
    });
    const order = ["lobes", "limbic", "subcortex", "brainstem", "language", "hemispheres", "networks", "peripheral", "tissue", "support"];
    let html = "";
    order.forEach((g) => {
      const items = byGroup[g];
      if (!items || !items.length) return;
      html += `<div class="anatomy-group"><span class="anatomy-group-title">${escapeHtml(ANATOMY_GROUPS[g] || g)}</span>`;
      items.forEach((s) => {
        const pct = Math.round((s.activity || 0) * 100);
        const tip = escapeHtml((s.role || "") + (s.note ? " — " + s.note : ""));
        html +=
          `<div class="anatomy-row" title="${tip}"><span>${escapeHtml(s.name)}</span>` +
          `<div class="bar"><i style="width:${pct}%"></i></div><span>${pct}%</span></div>`;
      });
      html += "</div>";
    });
    grid.innerHTML = html || "<p class='muted'>Sin datos…</p>";
    if (nt) {
      nt.innerHTML = (na.transmitters || [])
        .map((t) => {
          const pct = Math.round((t.level || 0) * 100);
          return (
            `<div class="anatomy-row nt"><span>${escapeHtml(t.name)}</span>` +
            `<div class="bar nt"><i style="width:${pct}%"></i></div><span>${pct}%</span></div>`
          );
        })
        .join("");
    }
  }

  function renderAffect(aff) {
    const felt = document.getElementById("affect-felt");
    const pools = document.getElementById("affect-pools");
    const log = document.getElementById("affect-log");
    if (!felt || !pools) return;
    if (!aff) {
      felt.textContent = "—";
      return;
    }
    felt.textContent = aff.felt || "—";
    const p = aff.pools || {};
    pools.innerHTML = Object.entries(AFFECT_LABELS)
      .map(([key, label]) => {
        const pool = p[key] || {};
        const bound = Math.round((pool.bound || 0) * 100);
        const syn = Math.round((pool.synaptic || 0) * 100);
        return (
          `<div class="affect-row"><span>${label}</span>` +
          `<div class="bar" title="receptor ${bound}%"><i style="width:${bound}%"></i></div>` +
          `<span class="muted" title="sináptico">${syn}%</span></div>`
        );
      })
      .join("");
    if (log) {
      const items = aff.process_log || [];
      log.innerHTML = items.length
        ? items.map((l) => `<li>${escapeHtml(l)}</li>`).join("")
        : "<li class='muted'>Sin liberaciones recientes…</li>";
    }
  }

  function renderLearning(log) {
    const el = document.getElementById("learning-log");
    if (!el) return;
    const items = log || [];
    el.innerHTML = items.length
      ? items.map((l) => `<li>${escapeHtml(l)}</li>`).join("")
      : "<li class='muted'>Sin aprendizajes recientes…</li>";
  }

  function renderSleepStudy(sleepStudy, data) {
    const logEl = document.getElementById("sleep-study-log");
    const statusEl = document.getElementById("sleep-study-status");
    if (!logEl) return;
    const ss = sleepStudy || {};
    const entries = ss.entries || ss.history || [];
    const bg = (data && data.sleep_study_background) || {};
    const pressure = data && data.hypothalamus ? data.hypothalamus.sleep_pressure : null;
    const env = data && data.environment ? data.environment : {};
    const atNight = env.phase === "night";
    if (statusEl) {
      const active = bg.active ? "background activo" : "en espera";
      const webOn = ss.enabled !== false ? " · web/nocturno ON" : "";
      statusEl.textContent =
        `${active}${webOn}` +
        (pressure != null ? ` · presión sueño ${Math.round(pressure * 100)}%` : "") +
        (atNight ? " · noche" : "");
    }
    logEl.innerHTML = entries.length
      ? entries
          .slice(0, 14)
          .map((e) => {
            const icon = e.icon || "💤";
            const label = e.label || e.title || "?";
            const snip = e.snippet ? `<span class="study-snippet">${escapeHtml(e.snippet)}</span>` : "";
            const meta = `<span class="study-meta">${escapeHtml(e.phase || "rem")} · ${escapeHtml(e.source || "sueño")}${e.remembered ? " · recordado" : ""}</span>`;
            return `<li>${icon} ${escapeHtml(label)}${snip}${meta}</li>`;
          })
          .join("")
      : "<li class='muted'>Aún no hay estudio nocturno — cuando duerma verás búsquedas y repasos aquí.</li>";
    if (dreamMode && dreamOverlay && entries[0]) {
      const latest = entries[0];
      const line = latest.label || latest.title || "";
      if (line && !dreamOverlay.querySelector("[data-sleep-study-last='" + line + "']")) {
        const span = document.createElement("span");
        span.className = "dream-study-line";
        span.dataset.sleepStudyLast = line;
        span.textContent = line;
        dreamOverlay.appendChild(span);
      }
    }
  }

  function renderTypedMemory(tm, sleepArch) {
    const flows = document.getElementById("circuit-flows");
    if (!flows || !tm) return;
    const sem = (tm.top_concepts || []).map((c) => c.label).slice(0, 2).join(", ");
    const proc = (tm.top_skills || []).map((s) => s.choice_key).slice(0, 2).join(", ");
    const phase = sleepArch && sleepArch.last_phase ? sleepArch.last_phase : "awake";
    const extra = document.getElementById("memory-types-hint");
    if (extra) {
      extra.textContent =
        `Memoria: semántica (${tm.semantic_count || 0}) · procedimental (${tm.procedural_count || 0}) · sueño: ${phase}`;
    }
    if (sem || proc) {
      const hint = document.createElement("li");
      hint.className = "muted";
      hint.textContent = (sem ? "Conceptos: " + sem : "") + (proc ? " · Hábitos: " + proc : "");
      if (flows.lastChild && flows.lastChild.className === "muted") flows.removeChild(flows.lastChild);
    }
  }

  function renderBrainFacts(bf, circuits) {
    const prog = document.getElementById("brain-facts-progress");
    const current = document.getElementById("brain-facts-current");
    const flows = document.getElementById("circuit-flows");
    if (!prog || !bf) return;
    const done = bf.completed || 0;
    const total = bf.total_chapters || 20;
    const pct = Math.round((bf.progress || done / total) * 100);
    prog.textContent = `Capítulos: ${done}/${total} (${pct}%) · ${bf.source || "SfN"}`;
    if (current) {
      const ch = bf.current || bf.next;
      if (ch) {
        current.innerHTML = ch.done
          ? `<span class="muted">Último:</span> ${escapeHtml(ch.title)}`
          : `<strong>Siguiente:</strong> ${escapeHtml(ch.title)}`;
      } else {
        current.textContent = "En el escritorio, con curiosidad, Nexo puede leer Brain Facts.";
      }
    }
    if (flows && circuits && circuits.top_flows) {
      flows.innerHTML = circuits.top_flows.length
        ? circuits.top_flows
            .slice(0, 5)
            .map(
              (f) =>
                `<li><span class="muted">${escapeHtml(f.from)}→${escapeHtml(f.to)}</span> ${escapeHtml(f.label)}</li>`
            )
            .join("")
        : "<li class='muted'>Circuitos en reposo…</li>";
    }
  }

  function renderAnatomyBook(ab) {
    const prog = document.getElementById("anatomy-book-progress");
    const current = document.getElementById("anatomy-book-current");
    const recent = document.getElementById("anatomy-book-recent");
    if (!prog || !ab) return;
    const done = ab.completed || 0;
    const total = ab.total_sections || 0;
    const pct = Math.round((ab.progress || (total ? done / total : 0)) * 100);
    prog.textContent = total
      ? `Progreso: ${done}/${total} secciones (${pct}%) — UCadiz 2022`
      : "Ejecuta scripts/ingest_anatomy_ucadiz.py para cargar el libro";
    if (current) {
      const cur = ab.current || ab.next;
      if (cur && cur.title) {
        current.innerHTML = `<strong>${cur.done ? "Última" : "Siguiente"}:</strong> ${escapeHtml(cur.title)}`;
      } else {
        current.textContent = "Nexo puede estudiar anatomía en el escritorio.";
      }
    }
    if (recent && ab.pending && ab.pending.length) {
      recent.innerHTML = ab.pending
        .slice(0, 4)
        .map((s) => `<li>${escapeHtml(s.title)} <span class="muted">p.${s.page_start}-${s.page_end}</span></li>`)
        .join("");
    }
  }

  function renderCurriculum(cur) {
    renderStudyTrack(cur, "curriculum", false, 46);
  }

  function renderStudyTrack(track, prefix, showPhases, fallbackTotal) {
    const prog = document.getElementById(`${prefix}-progress`);
    const current = document.getElementById(`${prefix}-current`);
    const recent = document.getElementById(`${prefix}-recent`);
    if (!prog || !track) return;
    const done = track.completed || 0;
    const total = track.total || fallbackTotal || done || 1;
    const pct = Math.round((track.progress || done / total) * 100);
    let progText = `Progreso: ${done}/${total} (${pct}%)`;
    if (showPhases && track.phases && track.phases.length) {
      progText += ` · fases: ${track.phases.join(" → ")}`;
    }
    prog.textContent = progText;
    if (current) {
      if (track.current_title) {
        const phase = track.sections && track.sections.find((s) => s.key === track.current_key);
        const phaseTag = phase && phase.phase ? ` <span class="muted">[${escapeHtml(phase.phase)}]</span>` : "";
        current.innerHTML = `<strong>En foco:</strong> ${escapeHtml(track.current_title)}${phaseTag}`;
      } else if (track.last_title) {
        current.innerHTML = `<span class="muted">Última:</span> ${escapeHtml(track.last_title)}`;
      } else {
        current.textContent = "Nexo puede estudiar esto en el escritorio.";
      }
    }
    if (recent && track.sections) {
      const pending = track.sections.filter((s) => !s.done).slice(0, 4);
      const doneList = track.sections.filter((s) => s.done).slice(-3).reverse();
      let html = "";
      if (doneList.length) {
        html += doneList.map((s) => `<li class="cur-done">✓ ${s.n}. ${escapeHtml(s.title)}</li>`).join("");
      }
      if (pending.length) {
        html += pending.map((s) => {
          const ph = s.phase ? ` <span class="muted">${escapeHtml(s.phase)}</span>` : "";
          return `<li class="cur-next">→ ${s.n}. ${escapeHtml(s.title)}${ph}</li>`;
        }).join("");
      }
      recent.innerHTML = html || "<li class='muted'>Ve al escritorio con curiosidad alta…</li>";
    }
  }

  function renderDialogue(data) {
    const el = document.getElementById("dialogue-log");
    if (!el) return;
    const turns = data.dialogue || [];
    if (!turns.length) {
      el.innerHTML = "<p class='muted'>Nexo y Nira aún no conversan…</p>";
      return;
    }
    el.innerHTML = turns
      .map(
        (t) =>
          `<div class="dialogue-turn${t.verbal ? " dialogue-verbal" : ""}">` +
          (t.verbal ? `<span class="dlg-tag">🗣 voz</span> ` : "") +
          `<span class="dlg-nexo">Nexo:</span> ${escapeHtml(t.nexo || "…")}<br>` +
          `<span class="dlg-nira">Nira:</span> ${escapeHtml(t.nira || "…")}</div>`
      )
      .join("");
  }

  function renderCognition(cog) {
    const focus = document.getElementById("cog-attention");
    const decision = document.getElementById("cog-decision");
    const predict = document.getElementById("cog-predict");
    const inner = document.getElementById("cog-inner");
    const delibEl = document.getElementById("cog-deliberation");
    if (!focus || !cog) return;
    const att = cog.attention || {};
    focus.textContent = att.focus ? att.focus + " (" + Math.round((att.salience || 0) * 100) + "%)" : "—";
    const dec = cog.decision || {};
    let decTxt = dec.choice ? dec.choice + " · " + Math.round((dec.confidence || 0) * 100) + "%" : "—";
    if (dec.agency != null) decTxt += " · libre albedrío " + Math.round(dec.agency * 100) + "%";
    if (dec.inhibited) decTxt += " · PFC frena impulso";
    decision.textContent = decTxt;
    const intentEl = document.getElementById("cog-intention");
    const ic = cog.intention_circuit;
    if (intentEl) {
      if (ic && ic.choice_key) {
        const align = ic.spike_aligned ? "spikes alineados" : "plantilla top-down";
        const veto = ic.pfc_veto ? " · PFC vetó impulso" : "";
        intentEl.textContent =
          "Circuito: " +
          ic.choice_key +
          " inyectado (" +
          Math.round((ic.sensory_gain || 0) * 100) +
          "%) · " +
          align +
          veto;
      } else {
        intentEl.textContent = "";
      }
    }
    const pred = cog.prediction || {};
    predict.textContent = pred.expected ? pred.expected + " · sorpresa " + Math.round((pred.surprise || 0) * 100) + "%" : "—";
    inner.textContent = cog.inner_voice || "—";
    const conEl = document.getElementById("cog-conscious");
    if (conEl && cog.consciousness) {
      const w = cog.consciousness.winner || {};
      const m = cog.consciousness.metacognition || {};
      conEl.textContent = w.label
        ? w.label + " · " + (m.felt || "—") + " · " + Math.round((w.salience || 0) * 100) + "%"
        : "—";
    }
    if (delibEl && cog.deliberation) {
      const d = cog.deliberation;
      const top = (d.contestants || []).slice(0, 3);
      delibEl.innerHTML = top.length
        ? top
            .map(
              (c) =>
                `<span class="delib-row${c.selected ? " delib-win" : ""}">` +
                `${escapeHtml(c.label)}: L${Math.round(c.limbic * 100)} PFC${Math.round(c.pfc * 100)} ` +
                `Go${Math.round(c.go * 100)} NoGo${Math.round(c.no_go * 100)}</span>`
            )
            .join("<br>")
        : "—";
    }
  }

  function renderCausalHud(hud) {
    const oneliner = document.getElementById("causal-oneliner");
    if (!oneliner) return;
    const h = hud || {};
    oneliner.textContent = h.one_liner || "—";
    const drive = document.getElementById("causal-drive");
    if (drive) {
      drive.textContent = h.top_drive
        ? `${h.top_drive} (${Math.round((h.top_drive_value || 0) * 100)}%)`
        : "—";
    }
    const choice = document.getElementById("causal-choice");
    if (choice) {
      choice.textContent = h.choice_key
        ? `${h.choice_key} · ${h.choice || ""}`
        : "—";
    }
    const agency = document.getElementById("causal-agency");
    if (agency) {
      agency.textContent =
        h.agency != null
          ? `${Math.round(h.agency * 100)}%${h.inhibited ? " · PFC frena impulso" : ""}`
          : "—";
    }
    const aff = document.getElementById("causal-aff");
    if (aff) {
      const biases = h.affordance_biases || {};
      const keys = Object.keys(biases);
      aff.textContent = keys.length
        ? `n=${h.affordance_records || 0} · ` +
          keys
            .slice(0, 3)
            .map((k) => `${k}:${biases[k] > 0 ? "+" : ""}${biases[k]}`)
            .join(" ")
        : `n=${h.affordance_records || 0}`;
    }
    const cf = document.getElementById("causal-cf");
    if (cf) {
      const preds = (h.counterfactual && h.counterfactual.predictions) || [];
      cf.textContent = preds.length
        ? preds
            .slice(0, 2)
            .map((p) => `${p.candidate_key} Δ${p.expected_homeostasis_gain}`)
            .join(" · ")
        : "—";
    }
    const guard = document.getElementById("causal-guard");
    if (guard && h.agency_guard) {
      guard.textContent = h.agency_guard.deliberation_selects_actions
        ? "PFC elige · LLM/affordances/CF no fuerzan"
        : "—";
    }
  }

  function renderObservatory(obs) {
    const panel = document.getElementById("observatory-panel");
    if (!panel || !obs || !Object.keys(obs).length) return;
    const oneliner = document.getElementById("obs-oneliner");
    if (oneliner) oneliner.textContent = obs.one_liner || "—";
    const tdEl = document.getElementById("obs-td");
    const td = obs.td || {};
    if (tdEl) {
      tdEl.textContent =
        td.last_delta != null
          ? `δ=${Number(td.last_delta).toFixed(3)} · V=${Object.keys(td.values || {}).length}`
          : "—";
    }
    const wmEl = document.getElementById("obs-wm");
    const wm = obs.working_memory || {};
    if (wmEl) {
      wmEl.textContent =
        wm.load != null
          ? `carga ${Math.round(wm.load * 100)}% · cap ${wm.capacity || "—"} · ${wm.slots ? wm.slots.length : 0} slots`
          : "—";
    }
    const attEl = document.getElementById("obs-attention");
    const att = obs.attention || {};
    if (attEl) {
      attEl.textContent =
        att.budget != null
          ? `budget ${att.budget} · focus ${att.focus_label || att.focus_source || "—"}`
          : "—";
    }
    const trEl = document.getElementById("obs-tracks");
    const prog = obs.track_progress || {};
    if (trEl) {
      const keys = Object.keys(prog);
      trEl.textContent = keys.length
        ? keys
            .sort((a, b) => prog[b] - prog[a])
            .slice(0, 4)
            .map((k) => `${k}:${Math.round(prog[k] * 100)}%`)
            .join(" · ")
        : "—";
    }
    const guard = document.getElementById("obs-guard");
    if (guard && obs.agency_guard) {
      guard.textContent = obs.agency_guard.deliberation_selects_actions
        ? "Telemetría observacional · PFC soberano"
        : "—";
    }
  }

  function renderAutonomy(log) {
    const el = document.getElementById("autonomy-log");
    if (!el) return;
    const items = log || [];
    el.innerHTML = items.length
      ? items.map((l) => `<li>${escapeHtml(l)}</li>`).join("")
      : "<li class='muted'>Nexo elige por sí mismo…</li>";
  }

  function renderDrives(drives) {
    if (!drives) return;
    const cur = document.getElementById("drive-curiosity");
    const goal = document.getElementById("drive-goal");
    if (cur) cur.textContent = drives.seek_curiosity != null ? Math.round(drives.seek_curiosity * 100) + "%" : "—";
    if (goal) {
      const best = Object.entries(drives).sort((a, b) => b[1] - a[1])[0];
      goal.textContent = best && best[1] > 0.25 ? best[0].replace("seek_", "") : "—";
    }
  }

  function renderArchetypeCardStats(t) {
    const el = document.getElementById("archetype-card-stats");
    if (!el || !t) return;
    el.textContent = `${t.internalized || 0} interiorizadas · ${t.uninternalized || 0} pendientes`;
  }

  async function plantEcho(text) {
    document.querySelectorAll("button").forEach((b) => (b.disabled = true));
    try {
      const j = await postJson("/api/echo", { text });
      updateHud(j);
      setHint("Eco sembrado — se integrará en su flujo interior");
      return j;
    } finally {
      document.querySelectorAll("button").forEach((b) => (b.disabled = false));
    }
  }

  async function worldTick() {
    if (ticking) return;
    ticking = true;
    try {
      const steps = turboActive || env.turbo ? 2 : 1;
      const j = await postJson("/api/world/tick", { steps });
      updateHud(j);
      if (j.world) applyWorld(j.world);
      if (typeof window.refreshExperienceJournal === "function") {
        window.refreshExperienceJournal();
      }
      return j;
    } catch (err) {
      console.error("worldTick:", err);
      setHint("Tick falló — reintentando… " + (err.message || err));
    } finally {
      ticking = false;
    }
  }

  window.showNexoBubble = (text) => showBubble(text, 12000);
  window.refreshWorldTick = worldTick;
  window.updateHud = updateHud;

  async function giveFile(file) {
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    fd.append("repeats", "3");
    document.querySelectorAll("button").forEach((b) => (b.disabled = true));
    try {
      const r = await fetch("/api/experience", { method: "POST", body: fd });
      const j = await r.json();
      if (!r.ok) throw new Error(j.error || r.statusText);
      updateHud(j);
      if (j.world) applyWorld(j.world);
      return j;
    } finally {
      document.querySelectorAll("button").forEach((b) => (b.disabled = false));
    }
  }

  async function giveFiles(fileList) {
    for (const f of fileList) {
      setHint("Aprendiendo: " + f.name);
      await giveFile(f);
    }
    setHint("Libros agregados al escritorio");
  }

  async function refreshLibrary() {
    const list = document.getElementById("library-list");
    if (!list) return;
    list.innerHTML = "<li class='muted'>Cargando…</li>";
    const r = await fetch("/api/library");
    const j = await r.json();
    const books = j.books || [];
    if (!books.length) {
      list.innerHTML = "<li class='muted'>Vacía — usa «Explorar archivos»</li>";
      return;
    }
    list.innerHTML = books
      .map((b) => `<li><span>${escapeHtml(b.name)}</span></li>`)
      .join("");
  }

  function hitNexo(x, y) {
    return Math.hypot(x - player.x, y - player.y) < 28;
  }

  function hitCompanion(x, y) {
    return Math.hypot(x - companion.x, y - companion.y) < 28;
  }

  function hitFurniture(x, y) {
    for (const fu of world.furniture || []) {
      if (fu.kind === "door") continue;
      if (x >= fu.x && x <= fu.x + fu.w && y >= fu.y && y <= fu.y + fu.h) return fu;
    }
    return null;
  }

  function hitObject(x, y) {
    for (const obj of world.objects || []) {
      if (Math.hypot(x - obj.x, y - obj.y) < 20) return obj;
    }
    return null;
  }

  const clickTarget = use3d && window.NexoRenderer && window.NexoRenderer.domElement
    ? window.NexoRenderer.domElement()
    : canvas;
  if (clickTarget && !use3d) {
    clickTarget.style.cursor = "crosshair";
  }

  function loop() {
    if (use3d && window.NexoRenderer && window.NexoRenderer.initialized()) {
      player.frame++;
      companion.frame = (companion.frame || 0) + 1;
      if (offspring) offspring.frame = (offspring.frame || 0) + 1;
      window.NexoRenderer.renderFrame({
        world,
        player,
        companion,
        offspring,
        env,
        vision: world.vision,
        dreamMode,
        dreamFragments,
      });
    } else if (ctx) {
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.clearRect(0, 0, W, H);
      drawGarden();
      drawHouseShell();
      (world.furniture || []).forEach(drawFurniture);
      (world.objects || []).forEach((obj) => {
        if (obj && Number.isFinite(obj.x) && Number.isFinite(obj.y)) drawObject(obj);
      });
      drawDreams();
      player.frame++;
      companion.frame = (companion.frame || 0) + 1;
      drawNexo(player);
      drawCompanion(companion);
      if (offspring) {
        offspring.frame = (offspring.frame || 0) + 1;
        drawOffspring(offspring);
      }
    }
    requestAnimationFrame(loop);
  }

  function bindBtn(id, fn) {
    const el = document.getElementById(id);
    if (el) el.addEventListener("click", fn);
  }

  const libPanel = document.getElementById("library-panel");
  document.getElementById("btn-say").onclick = async () => {
    const inp = document.getElementById("chat-in");
    const msg = inp.value.trim();
    if (!msg) return;
    if (window.caregiverSensors && window.caregiverSensors.sendSpeech) {
      await window.caregiverSensors.sendSpeech(msg);
    } else {
      await plantEcho(msg);
    }
    inp.value = "";
  };
  document.getElementById("chat-in").addEventListener("keydown", (e) => {
    if (e.key === "Enter") document.getElementById("btn-say").click();
  });

  bindBtn("btn-reborn", async () => {
    const j = await postJson("/api/lifecycle/reborn", {});
    updateHud(j);
    if (j.world) applyWorld(j.world);
    setHint("Nuevo ciclo vital");
  });

  bindBtn("btn-faint", async () => {
    const btn = document.getElementById("btn-faint");
    if (btn) {
      btn.disabled = true;
      btn.textContent = "Desmayándose…";
    }
    try {
      const out = await postJson("/api/faint", {});
      if (out.learned) {
        setHint("Aprendió «" + out.recall.token + "». Está en la memoria.");
      } else if (out.held) {
        setHint("Se desmayó, pero no quedó la frase en la memoria.");
      } else {
        setHint("Se desmayó. El estante de los nodos estaba vacío.");
      }
      showBubble(out.message || "Se desmayó.", 8000);
    } catch (err) {
      setHint("El desmayo no se completó.");
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = "Desmayo";
      }
    }
  });

  bindBtn("btn-library", () => {
    if (libPanel) libPanel.classList.remove("hidden");
    refreshLibrary();
  });
  bindBtn("btn-lib-close", () => { if (libPanel) libPanel.classList.add("hidden"); });
  bindBtn("btn-lib-refresh", refreshLibrary);
  const libImport = document.getElementById("lib-import");
  if (libImport) {
    libImport.onchange = async (e) => {
      const files = e.target.files;
      if (!files || !files.length) return;
      for (const f of files) {
        const fd = new FormData();
        fd.append("file", f);
        await fetch("/api/library/import", { method: "POST", body: fd });
      }
      e.target.value = "";
      await refreshLibrary();
      setHint("Archivos archivados en biblioteca");
    };
  }

  setHint("Observando a Nexo — modo autónomo");
  bindTimeline();
  fetch("/api/time")
    .then((r) => r.json())
    .then((j) => {
      if (j.environment) applyEnvironment(j.environment);
      if (j.temporal) renderTemporal(j.temporal);
    })
    .catch(() => {});
  loop();
  scheduleTicks();
  refreshImaginationFrame();
  setInterval(refreshImaginationFrame, 2200);

  fetch("/api/world")
    .then((r) => r.json())
    .then((w) => { applyWorld(w); return fetch("/api/state"); })
    .then((r) => r.json())
    .then((s) => { updateHud(s); if (s.world) applyWorld(s.world); })
    .catch(() => applyWorld({ furniture: DEFAULT_FURNITURE, agent: { x: 120, y: 220, dir: 1 } }));
  worldTick().catch(() => {});
})();
