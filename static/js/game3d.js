/**
 * Vista 3D del hogar de Nexo (Three.js) — orbitar, zoom e inspección.
 */
(function () {
  const SCALE = 0.1;
  const HOUSE_X = 168 * SCALE;

  const FURN_COLORS = {
    desk: 0x6d4c33,
    tv: 0x263238,
    fridge: 0xb0bec5,
    bed: 0x7986cb,
    sofa: 0xa1887f,
    door: 0x4e342e,
    bath: 0x81d4fa,
    toilet: 0xe0e0e0,
    stove: 0x455a64,
  };

  let scene, camera, renderer, container;
  let agentMesh, companionMesh, offspringMesh;
  let furnitureMeshes = [];
  let objectMeshes = [];
  let treeMeshes = [];
  let houseShellMeshes = [];
  let sunLight, ambLight;
  let gazeCone = null;
  let initialized = false;
  let worldSig = "";
  let lastWorld = null;
  let divineLight = null;
  let divineBeam = null;
  let divineIntensity = 0;
  const procTexCache = {};

  const HOUSE_BOUNDS = {
    xMin: HOUSE_X,
    xMax: HOUSE_X + 47,
    yMin: 0,
    yMax: 2.5,
    zMin: 0,
    zMax: 40,
  };

  const orbit = {
    yaw: -0.85,
    pitch: 0.22,
    distance: 42,
    targetY: 1.5,
  };

  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();

  function to3(x, y) {
    return { x: x * SCALE, z: y * SCALE };
  }

  function clamp(v, lo, hi) {
    return Math.max(lo, Math.min(hi, v));
  }

  function viewportSize() {
    if (!container) return { w: 640, h: 400 };
    const w = Math.max(320, container.clientWidth || 640);
    const h = Math.max(240, container.clientHeight || 400);
    return { w, h };
  }

  function resize() {
    if (!renderer || !camera || !container) return;
    const { w, h } = viewportSize();
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h, false);
  }

  function bindOrbit(el) {
    el.style.cursor = "grab";
    el.style.touchAction = "none";

    let dragging = false;
    let panning = false;
    let lastX = 0;
    let lastY = 0;
    let dragMoved = 0;

    el.addEventListener("pointerdown", (e) => {
      if (e.button === 0 || e.button === 2) {
        dragging = true;
        panning = e.button === 2;
        dragMoved = 0;
        lastX = e.clientX;
        lastY = e.clientY;
        el.setPointerCapture(e.pointerId);
        el.style.cursor = panning ? "move" : "grabbing";
      }
    });

    el.addEventListener("pointermove", (e) => {
      if (!dragging) return;
      const dx = e.clientX - lastX;
      const dy = e.clientY - lastY;
      dragMoved += Math.abs(dx) + Math.abs(dy);
      lastX = e.clientX;
      lastY = e.clientY;
      if (panning) {
        orbit.yaw -= dx * 0.004;
        orbit.pitch = clamp(orbit.pitch + dy * 0.004, 0.12, 1.05);
      } else {
        orbit.yaw -= dx * 0.006;
        orbit.pitch = clamp(orbit.pitch + dy * 0.006, 0.12, 1.05);
      }
    });

    const endDrag = (e) => {
      if (!dragging) return;
      const wasClick = dragMoved < 6;
      dragging = false;
      panning = false;
      el.style.cursor = "grab";
      try {
        el.releasePointerCapture(e.pointerId);
      } catch (_) {
        /* ignore */
      }
      if (wasClick && e.button === 0) {
        const hit = pickAt(e.clientX, e.clientY);
        if (hit && onPick) onPick(hit);
      }
    };
    el.addEventListener("pointerup", endDrag);
    el.addEventListener("pointercancel", endDrag);
    el.addEventListener("pointerleave", endDrag);

    el.addEventListener(
      "wheel",
      (e) => {
        e.preventDefault();
        orbit.distance = clamp(orbit.distance + e.deltaY * 0.025, 10, 78);
      },
      { passive: false }
    );

    el.addEventListener("contextmenu", (e) => e.preventDefault());
  }

  function pointInsideHouse(x, y, z, pad) {
    const m = pad || 0;
    return (
      x > HOUSE_BOUNDS.xMin - m &&
      x < HOUSE_BOUNDS.xMax + m &&
      y > HOUSE_BOUNDS.yMin - m &&
      y < HOUSE_BOUNDS.yMax + m &&
      z > HOUSE_BOUNDS.zMin - m &&
      z < HOUSE_BOUNDS.zMax + m
    );
  }

  /** Empuja la cámara fuera solo en vistas laterales; vista cenital permite ver el interior. */
  function resolveCameraPosition(pos, focus) {
    const out = pos.clone();
    if (orbit.pitch >= 0.3) {
      out.y = Math.max(out.y, 3.5);
      return out;
    }
    if (!pointInsideHouse(out.x, out.y, out.z, 0.5)) {
      out.y = Math.max(out.y, 6);
      return out;
    }
    const west = Math.abs(out.x - HOUSE_BOUNDS.xMin);
    const east = Math.abs(HOUSE_BOUNDS.xMax - out.x);
    const south = Math.abs(out.z - HOUSE_BOUNDS.zMin);
    const north = Math.abs(HOUSE_BOUNDS.zMax - out.z);
    const minEdge = Math.min(west, east, south, north);
    const margin = 4;
    if (minEdge === west) out.x = HOUSE_BOUNDS.xMin - margin;
    else if (minEdge === east) out.x = HOUSE_BOUNDS.xMax + margin;
    else if (minEdge === south) out.z = HOUSE_BOUNDS.zMin - margin;
    else out.z = HOUSE_BOUNDS.zMax + margin;
    out.y = Math.max(out.y, 12);
    if (pointInsideHouse(out.x, out.y, out.z, 0)) {
      out.x = HOUSE_BOUNDS.xMin - margin;
      out.y = 18;
      out.z = focus.z + 6;
    }
    return out;
  }

  function updateCameraFocus(x, y) {
    const p = to3(x, y);
    const r = orbit.distance;
    const yOff = orbit.targetY + r * Math.cos(orbit.pitch);
    const horiz = r * Math.sin(orbit.pitch);
    const raw = new THREE.Vector3(
      p.x + horiz * Math.sin(orbit.yaw),
      yOff,
      p.z + horiz * Math.cos(orbit.yaw)
    );
    const pos = resolveCameraPosition(raw, p);
    camera.position.copy(pos);
    camera.lookAt(p.x, orbit.targetY, p.z);
  }

  function pickables() {
    const out = [];
    if (agentMesh) out.push({ mesh: agentMesh, label: "Nexo", kind: "agent" });
    if (companionMesh) out.push({ mesh: companionMesh, label: "Nira", kind: "companion" });
    if (offspringMesh && offspringMesh.visible) {
      out.push({ mesh: offspringMesh, label: "Cría", kind: "offspring" });
    }
    furnitureMeshes.forEach((m, i) => {
      out.push({
        mesh: m,
        label: m.userData.label || "mueble",
        kind: "furniture",
        qualities: m.userData.qualities,
        index: i,
      });
    });
    objectMeshes.forEach((m, i) => {
      out.push({
        mesh: m,
        label: m.userData.label || "objeto",
        kind: "object",
        qualities: m.userData.qualities,
        index: i,
      });
    });
    return out;
  }

  function pickAt(clientX, clientY) {
    if (!renderer || !camera) return null;
    const rect = renderer.domElement.getBoundingClientRect();
    pointer.x = ((clientX - rect.left) / rect.width) * 2 - 1;
    pointer.y = -((clientY - rect.top) / rect.height) * 2 + 1;
    raycaster.setFromCamera(pointer, camera);
    const items = pickables();
    const meshes = items.map((i) => i.mesh);
    const hits = raycaster.intersectObjects(meshes, true);
    if (!hits.length) return null;
    const root = hits[0].object;
    let node = root;
    while (node.parent && node.parent !== scene) node = node.parent;
    const match = items.find((i) => i.mesh === node || i.mesh === root || node.parent === i.mesh);
    return match || { mesh: root, label: "algo", kind: "unknown" };
  }

  function addShell(mesh) {
    scene.add(mesh);
    houseShellMeshes.push(mesh);
    return mesh;
  }

  function tryBlenderHouse() {
    if (!scene || typeof THREE.GLTFLoader === "undefined") return;
    fetch("/api/world3d/model")
      .then((res) => (res.ok ? res.arrayBuffer() : null))
      .then((buf) => {
        if (!buf) return;
        const loader = new THREE.GLTFLoader();
        loader.parse(buf, "", (gltf) => {
          const root = gltf.scene;
          const cx = (HOUSE_BOUNDS.xMin + HOUSE_BOUNDS.xMax) / 2;
          const cz = (HOUSE_BOUNDS.zMin + HOUSE_BOUNDS.zMax) / 2;
          root.position.set(cx, 0, cz);
          root.name = "blender-house";
          scene.add(root);
          houseShellMeshes.forEach((m) => {
            m.visible = false;
          });
        });
      })
      .catch(() => {});
  }

  function wallBox(w, h, d, x, y, z, mat) {
    const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
    m.position.set(x, y, z);
    m.castShadow = true;
    m.receiveShadow = true;
    return addShell(m);
  }

  function makeWindow(cx, cy, cz, width, height, facingX) {
    const g = new THREE.Group();
    const frameMat = stdMat(0x5d4037, 0.85);
    const glassMat = new THREE.MeshStandardMaterial({
      color: 0x90caf9,
      roughness: 0.15,
      metalness: 0.2,
      transparent: true,
      opacity: 0.55,
      emissive: 0x42a5f5,
      emissiveIntensity: 0.12,
    });
    const fw = width;
    const fh = height;
    const ft = 0.06;
    const top = new THREE.Mesh(new THREE.BoxGeometry(fw + ft * 2, ft, ft), frameMat);
    top.position.y = fh / 2;
    const bot = top.clone();
    bot.position.y = -fh / 2;
    const left = new THREE.Mesh(new THREE.BoxGeometry(ft, fh, ft), frameMat);
    left.position.x = -fw / 2;
    const right = left.clone();
    right.position.x = fw / 2;
    const glass = new THREE.Mesh(new THREE.BoxGeometry(fw * 0.92, fh * 0.88, 0.04), glassMat);
    const sill = new THREE.Mesh(new THREE.BoxGeometry(fw + 0.2, 0.05, 0.14), frameMat);
    sill.position.y = -fh / 2 - 0.06;
    g.add(top, bot, left, right, glass, sill);
    g.position.set(cx, cy, cz);
    if (facingX) g.rotation.y = Math.PI / 2;
    addShell(g);
    return g;
  }

  function makeDoor(cx, cz, height, width) {
    const g = new THREE.Group();
    const frameMat = stdMat(0x4e342e, 0.88);
    const doorMat = stdMat(0x6d4c41, 0.82);
    const ft = 0.1;
    const jambL = new THREE.Mesh(new THREE.BoxGeometry(ft, height, width + ft * 2), frameMat);
    jambL.position.set(-ft / 2, height / 2, 0);
    const jambR = jambL.clone();
    jambR.position.x = ft / 2;
    const lintel = new THREE.Mesh(new THREE.BoxGeometry(ft * 2.2, ft, width + ft * 2), frameMat);
    lintel.position.y = height;
    const panel = new THREE.Mesh(new THREE.BoxGeometry(0.12, height * 0.92, width * 0.88), doorMat);
    panel.position.set(0.08, height * 0.46, 0);
    const knob = new THREE.Mesh(
      new THREE.SphereGeometry(0.06, 8, 8),
      new THREE.MeshStandardMaterial({ color: 0xffd54f, metalness: 0.7, roughness: 0.3 })
    );
    knob.position.set(0.18, height * 0.45, width * 0.32);
    const mat = new THREE.Mesh(new THREE.BoxGeometry(width + 0.3, 0.04, 0.5), stdMat(0x795548, 0.9));
    mat.position.set(0.25, 0.02, 0.35);
    g.add(jambL, jambR, lintel, panel, knob, mat);
    g.position.set(cx, 0, cz);
    g.rotation.y = Math.PI / 2;
    addShell(g);
    return g;
  }

  function roomFloor(x0, x1, z0, z1, color, y) {
    const w = x1 - x0;
    const d = z1 - z0;
    const m = new THREE.Mesh(
      new THREE.BoxGeometry(w, 0.04, d),
      new THREE.MeshStandardMaterial({ color, roughness: 0.82, metalness: 0.02 })
    );
    m.position.set((x0 + x1) / 2, y || 0.27, (z0 + z1) / 2);
    m.receiveShadow = true;
    return addShell(m);
  }

  function roomLabel(x, z, text, color) {
    const g = new THREE.Group();
    const pole = new THREE.Mesh(
      new THREE.BoxGeometry(0.04, 0.55, 0.04),
      stdMat(color, 0.9)
    );
    pole.position.y = 0.28;
    const sign = new THREE.Mesh(
      new THREE.BoxGeometry(0.9, 0.22, 0.04),
      new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: 0.25 })
    );
    sign.position.y = 0.62;
    g.add(pole, sign);
    g.position.set(x, 0, z);
    g.userData.label = text;
    return addShell(g);
  }

  function interiorWall(w, h, d, x, y, z, mat, gap) {
    if (gap) {
      const seg = (d - gap.size) / 2;
      if (seg > 0.1) {
        wallBox(w, h, seg, x, y, z - d / 2 + seg / 2, mat);
        wallBox(w, h, seg, x, y, z + d / 2 - seg / 2, mat);
      }
      return;
    }
    wallBox(w, h, d, x, y, z, mat);
  }

  function buildNexoHome() {
    const HX0 = 17.5;
    const HX1 = 64;
    const HZ0 = 0;
    const HZ1 = 40;
    const wallH = 2.35;
    const wallY = wallH / 2;
    const thick = 0.22;
    const extMat = new THREE.MeshStandardMaterial({
      color: 0xf5f0e6,
      roughness: 0.9,
      transparent: true,
      opacity: 0.2,
      depthWrite: false,
      side: THREE.DoubleSide,
    });
    const intMat = new THREE.MeshStandardMaterial({
      color: 0xd7ccc8,
      roughness: 0.95,
      transparent: true,
      opacity: 0.45,
      depthWrite: false,
    });
    const trimMat = stdMat(0x8d6e63, 0.92);
    const roofMat = new THREE.MeshStandardMaterial({ color: 0x6d4c41, roughness: 0.88 });

    // —— Jardín ——
    const garden = new THREE.Mesh(
      new THREE.PlaneGeometry(HX0 + 8, HZ1 + 6),
      new THREE.MeshStandardMaterial({ color: 0x4caf50, roughness: 0.95 })
    );
    garden.rotation.x = -Math.PI / 2;
    garden.position.set((HX0 + 8) / 2 - 2, 0.01, HZ1 / 2);
    garden.receiveShadow = true;
    scene.add(garden);

    const path = new THREE.Mesh(
      new THREE.PlaneGeometry(2.2, 14),
      stdMat(0xbdbdbd, 0.95)
    );
    path.rotation.x = -Math.PI / 2;
    path.position.set(HX0 - 0.8, 0.02, 20);
    scene.add(path);

    for (let i = 0; i < 6; i++) {
      const tx = 3 + (i % 3) * 4.5;
      const tz = 4 + Math.floor(i / 3) * 14;
      const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.2, 1.6, 8), stdMat(0x5d4037));
      trunk.position.set(tx, 0.8, tz);
      trunk.castShadow = true;
      const crown = new THREE.Mesh(new THREE.ConeGeometry(1.1, 2.2, 8), stdMat(0x2e7d32, 0.9));
      crown.position.set(tx, 2.2, tz);
      crown.castShadow = true;
      scene.add(trunk, crown);
    }

    // —— Suelos por habitación (colores distintos) ——
    roomFloor(HX0, 30, 14, HZ1, 0xd7ccc8, 0.27); // entrada / salón
    roomFloor(30, 48, 14, HZ1, 0xffe0b2, 0.27); // cocina-comedor
    roomFloor(48, HX1, 14, HZ1, 0xc5cae9, 0.27); // dormitorio
    roomFloor(HX0, 48, HZ0, 14, 0xe3f2fd, 0.27); // zona norte (TV + baño)
    roomFloor(48, HX1, HZ0, 14, 0xfff9c4, 0.27); // escritorio
    roomFloor(30, 48, HZ0, 14, 0xb3e5fc, 0.27); // baño

    roomLabel(24, 32, "Salón", 0x8d6e63);
    roomLabel(38, 32, "Cocina", 0xff8f00);
    roomLabel(56, 32, "Dormitorio", 0x5c6bc0);
    roomLabel(44, 31, "Baño", 0x0288d1);
    roomLabel(56, 8, "Escritorio", 0xf9a825);
    roomLabel(34, 11, "Sala TV", 0x37474f);
    roomLabel(8, 20, "Jardín", 0x2e7d32);

    // —— Tabiques interiores ——
    interiorWall(thick, wallH, HZ1 - 14, 30, wallY, (14 + HZ1) / 2, intMat);
    interiorWall(thick, wallH, HZ1 - 14, 48, wallY, (14 + HZ1) / 2, intMat);
    interiorWall(thick, wallH, 48 - HX0, (HX0 + 30) / 2, wallY, 14, intMat, { size: 2.2 });
    interiorWall(thick, wallH, HX1 - 48, 48, wallY, 14, intMat, { size: 1.8 });
    interiorWall(thick, wallH * 0.85, 14, (30 + 48) / 2, wallY * 0.92, 14, intMat, { size: 2.4 });

    // —— Muros exteriores ——
    const cx = (HX0 + HX1) / 2;
    const cz = (HZ0 + HZ1) / 2;
    wallBox(HX1 - HX0, wallH, thick, cx, wallY, HZ0, extMat);
    wallBox(HX1 - HX0, wallH, thick, cx, wallY, HZ1, extMat);
    wallBox(thick, wallH, HZ1 - HZ0, HX1, wallY, cz, extMat);
    const doorZ0 = 16.5;
    const doorZ1 = 23.5;
    wallBox(thick, wallH, doorZ0 - HZ0, HX0, wallY, HZ0 + (doorZ0 - HZ0) / 2, extMat);
    wallBox(thick, wallH, HZ1 - doorZ1, HX0, wallY, doorZ1 + (HZ1 - doorZ1) / 2, extMat);
    makeDoor(HX0 + 0.15, (doorZ0 + doorZ1) / 2, 2.0, doorZ1 - doorZ0);

    makeWindow(cx - 10, wallY + 0.2, HZ0 + 0.12, 2.2, 0.95, false);
    makeWindow(cx + 8, wallY + 0.2, HZ0 + 0.12, 1.8, 0.85, false);
    makeWindow(cx - 6, wallY + 0.2, HZ1 - 0.12, 2.0, 0.9, false);
    makeWindow(HX1 - 0.12, wallY + 0.25, cz + 6, 1.6, 0.85, true);
    makeWindow(HX1 - 0.12, wallY + 0.25, cz - 8, 1.4, 0.75, true);

    // Techo omitido — vista tipo «muñeca» para ver habitaciones y muebles
    const roofOutlineMat = new THREE.MeshBasicMaterial({
      color: 0x6d4c41,
      wireframe: true,
      transparent: true,
      opacity: 0.35,
    });
    const roofOutline = new THREE.Mesh(
      new THREE.BoxGeometry(HX1 - HX0 + 0.4, 0.08, HZ1 - HZ0 + 0.4),
      roofOutlineMat
    );
    roofOutline.position.set(cx, wallH + 0.12, cz);
    addShell(roofOutline);

    const porch = new THREE.Mesh(new THREE.BoxGeometry(1.8, 0.1, 8), trimMat);
    porch.position.set(HX0 - 0.6, 2.05, 20);
    addShell(porch);

    const chimney = new THREE.Mesh(new THREE.BoxGeometry(0.5, 1.1, 0.5), stdMat(0x5d4037));
    chimney.position.set(HX1 - 6, wallH + 0.9, cz - 10);
    addShell(chimney);

    // —— Luces por habitación ——
    [
      [24, 28, 0xfff3e0],
      [38, 28, 0xffe082],
      [56, 28, 0xe8eaf6],
      [38, 6, 0xe1f5fe],
      [56, 6, 0xfffde7],
    ].forEach(([x, z, col]) => {
      const bulb = new THREE.PointLight(col, 0.35, 14);
      bulb.position.set(x, wallH - 0.15, z);
      scene.add(bulb);
      const fixture = new THREE.Mesh(
        new THREE.CylinderGeometry(0.12, 0.18, 0.08, 10),
        new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: col, emissiveIntensity: 0.4 })
      );
      fixture.position.set(x, wallH - 0.05, z);
      addShell(fixture);
    });

    const fenceMat = stdMat(0x6d4c41);
    for (let z = 2; z < HZ1; z += 4) {
      const post = new THREE.Mesh(new THREE.BoxGeometry(0.07, 0.65, 0.07), fenceMat);
      post.position.set(HX0 - 1.2, 0.33, z);
      addShell(post);
    }

    HOUSE_BOUNDS.xMin = HX0;
    HOUSE_BOUNDS.xMax = HX1;
    HOUSE_BOUNDS.zMin = HZ0;
    HOUSE_BOUNDS.zMax = HZ1;
    HOUSE_BOUNDS.yMax = wallH + 0.5;
  }

  function buildHouseArchitecture() {
    buildNexoHome();
  }

  function buildInteriorDetails() {
    /* integrado en buildNexoHome */
  }

  function init(el) {
    if (!el || typeof THREE === "undefined") return false;
    try {
      container = el;
      const { w, h } = viewportSize();

    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x87ceeb);
    scene.fog = new THREE.Fog(0x87ceeb, 45, 120);

    camera = new THREE.PerspectiveCamera(48, w / h, 0.1, 200);
    camera.position.set(28, 22, 48);

    orbit.yaw = -0.72;
    orbit.pitch = 0.62;
    orbit.distance = 44;
    orbit.targetY = 1.0;

    renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
    renderer.setSize(w, h, false);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    el.appendChild(renderer.domElement);
    bindOrbit(renderer.domElement);

    if (typeof ResizeObserver !== "undefined") {
      new ResizeObserver(() => resize()).observe(el);
    } else {
      window.addEventListener("resize", resize);
    }

    ambLight = new THREE.AmbientLight(0xffffff, 0.55);
    scene.add(ambLight);
    const hemi = new THREE.HemisphereLight(0xbfd9ff, 0x5a7a3a, 0.55);
    scene.add(hemi);
    sunLight = new THREE.DirectionalLight(0xfff5e0, 0.9);
    sunLight.position.set(20, 40, 15);
    sunLight.castShadow = true;
    sunLight.shadow.mapSize.width = 2048;
    sunLight.shadow.mapSize.height = 2048;
    scene.add(sunLight);

    buildNexoHome();
    tryBlenderHouse();

    ensureDivineLight();

    agentMesh = makeApe(0xf4d03f, 0.9);
    companionMesh = makeApe(0xe1bee7, 0.85);
    offspringMesh = makeApe(0xffcc80, 0.55);
    scene.add(agentMesh);
    scene.add(companionMesh);
    scene.add(offspringMesh);
    offspringMesh.visible = false;

    gazeCone = new THREE.Mesh(
      new THREE.ConeGeometry(3, 8, 8, 1, true),
      new THREE.MeshBasicMaterial({ color: 0xffff88, transparent: true, opacity: 0.12, depthWrite: false })
    );
    gazeCone.rotation.x = -Math.PI / 2;
    scene.add(gazeCone);

    initialized = true;
    resize();
    return true;
    } catch (err) {
      console.error("NexoRenderer init failed:", err);
      if (renderer && renderer.domElement && renderer.domElement.parentNode) {
        renderer.domElement.parentNode.removeChild(renderer.domElement);
      }
      renderer = null;
      scene = null;
      initialized = false;
      return false;
    }
  }

  function capsuleGeo(radius, length, capSegments, radialSegments) {
    if (typeof THREE.CapsuleGeometry === "function") {
      return new THREE.CapsuleGeometry(radius, length, capSegments || 4, radialSegments || 8);
    }
    const g = new THREE.CylinderGeometry(radius, radius, length + radius * 2, radialSegments || 8);
    return g;
  }

  function stdMat(color, roughness) {
    return new THREE.MeshStandardMaterial({ color, roughness: roughness != null ? roughness : 0.78 });
  }

  function procTexture(kind) {
    if (procTexCache[kind]) return procTexCache[kind];
    const c = document.createElement("canvas");
    c.width = c.height = 128;
    const ctx = c.getContext("2d");
    const rng = (n) => ((n * 9301 + 49297) % 233280) / 233280;

    if (kind === "roble" || kind === "madera") {
      ctx.fillStyle = "#6d4c33";
      ctx.fillRect(0, 0, 128, 128);
      for (let y = 0; y < 128; y++) {
        const v = 0.85 + rng(y) * 0.3;
        ctx.strokeStyle = `rgba(40,25,15,${0.08 + rng(y + 7) * 0.12})`;
        ctx.beginPath();
        ctx.moveTo(0, y);
        for (let x = 0; x < 128; x += 4) {
          ctx.lineTo(x, y + Math.sin(x * 0.08 + y * 0.02) * 2 * v);
        }
        ctx.stroke();
      }
    } else if (kind === "terciopelo" || kind === "algodón" || kind === "textil") {
      ctx.fillStyle = kind === "terciopelo" ? "#8d6e63" : "#e8eaf6";
      ctx.fillRect(0, 0, 128, 128);
      for (let i = 0; i < 800; i++) {
        const x = rng(i) * 128;
        const y = rng(i + 3) * 128;
        ctx.fillStyle = `rgba(0,0,0,${0.02 + rng(i + 9) * 0.04})`;
        ctx.fillRect(x, y, 1, 2);
      }
    } else if (kind === "porcelana" || kind === "cerámica") {
      const g = ctx.createLinearGradient(0, 0, 128, 128);
      g.addColorStop(0, "#f5f5f5");
      g.addColorStop(1, "#b3e5fc");
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, 128, 128);
    } else if (kind === "acero cepillado" || kind === "metal" || kind === "hierro fundido") {
      const g = ctx.createLinearGradient(0, 0, 128, 0);
      g.addColorStop(0, "#cfd8dc");
      g.addColorStop(0.5, "#90a4ae");
      g.addColorStop(1, "#eceff1");
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, 128, 128);
      for (let i = 0; i < 60; i++) {
        ctx.strokeStyle = `rgba(255,255,255,${0.05 + rng(i) * 0.08})`;
        ctx.beginPath();
        ctx.moveTo(rng(i + 1) * 128, 0);
        ctx.lineTo(rng(i + 2) * 128, 128);
        ctx.stroke();
      }
    } else {
      ctx.fillStyle = "#888";
      ctx.fillRect(0, 0, 128, 128);
    }

    const tex = new THREE.CanvasTexture(c);
    tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
    tex.repeat.set(2, 2);
    procTexCache[kind] = tex;
    return tex;
  }

  function tempToEmissive(q) {
    const t = (q && q.temperature_c) || 20;
    if (t > 40) return { color: 0xff5722, intensity: Math.min(1.2, (t - 40) / 50) };
    if (t < 12) return { color: 0x81d4fa, intensity: Math.min(0.35, (12 - t) / 12) };
    return null;
  }

  function matFromQualities(q, colorOverride) {
    const color = colorOverride != null ? colorOverride : FURN_COLORS[(q && q.kind) || "desk"] || 0x888888;
    const texKey = (q && q.texture) || "madera";
    const map = procTexture(texKey.split(" ")[0] === "acero" ? "acero cepillado" : texKey.split(" ")[0]);
    const em = tempToEmissive(q);
    const mat = new THREE.MeshStandardMaterial({
      color,
      map,
      roughness: (q && q.roughness) != null ? q.roughness : 0.78,
      metalness: (q && q.metalness) != null ? q.metalness : 0.05,
    });
    if ((q && q.emissive) || em) {
      mat.emissive = new THREE.Color(em ? em.color : 0xfff3e0);
      mat.emissiveIntensity = em ? em.intensity : 0.25;
    }
    return mat;
  }

  function formatQualitiesLabel(q) {
    if (window.NexoMaterialQualities) return window.NexoMaterialQualities.formatQualities(q);
    if (!q) return "";
    return [q.texture, q.temperature_c != null ? q.temperature_c + "°C" : "", q.feels].filter(Boolean).join(" · ");
  }

  function resolveFuQ(fu, world) {
    if (fu.qualities) return fu.qualities;
    if (window.NexoMaterialQualities) return window.NexoMaterialQualities.resolveFurnitureQualities(fu, world);
    return { kind: fu.kind, texture: "madera", temperature_c: 20, roughness: 0.8 };
  }

  function setDivineVoice(intensity) {
    divineIntensity = Math.max(0, Math.min(1, intensity || 0));
    if (!divineLight) return;
    divineLight.intensity = 0.2 + divineIntensity * 2.2;
    if (divineBeam && divineBeam.material) {
      divineBeam.material.opacity = 0.06 + divineIntensity * 0.22;
    }
  }

  function ensureDivineLight() {
    if (divineLight) return;
    divineLight = new THREE.PointLight(0xfff8e1, 0, 55, 2);
    divineLight.position.set(40, 22, 20);
    scene.add(divineLight);
    const beamGeo = new THREE.CylinderGeometry(0.05, 2.8, 18, 16, 1, true);
    divineBeam = new THREE.Mesh(
      beamGeo,
      new THREE.MeshBasicMaterial({
        color: 0xfffde7,
        transparent: true,
        opacity: 0.08,
        side: THREE.DoubleSide,
        depthWrite: false,
      })
    );
    divineBeam.position.set(40, 11, 20);
    scene.add(divineBeam);
    if (window.SkyVoice) window.SkyVoice.setSkyPosition(40, 22, 20);
  }

  function makeApe(color, scale) {
    const g = new THREE.Group();
    const skin = stdMat(0xffe082, 0.82);
    const fur = stdMat(color, 0.86);

    const pelvis = new THREE.Group();
    pelvis.position.y = 0.95 * scale;

    const spine = new THREE.Group();
    spine.position.y = 0.08 * scale;
    pelvis.add(spine);

    const torso = new THREE.Mesh(capsuleGeo(0.42 * scale, 0.75 * scale, 4, 8), fur);
    torso.position.y = 0.12 * scale;
    torso.castShadow = true;
    spine.add(torso);

    const headGroup = new THREE.Group();
    headGroup.position.y = 0.52 * scale;
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.38 * scale, 12, 10), skin);
    head.position.y = 0.42 * scale;
    head.castShadow = true;
    const snout = new THREE.Mesh(new THREE.BoxGeometry(0.22 * scale, 0.14 * scale, 0.18 * scale), skin);
    snout.position.set(0, 0.35 * scale, 0.24 * scale);
    snout.castShadow = true;
    const eyeGeo = new THREE.SphereGeometry(0.05 * scale, 6, 6);
    const eyeMat = new THREE.MeshStandardMaterial({ color: 0x1a1a1a, roughness: 0.4 });
    const eyeL = new THREE.Mesh(eyeGeo, eyeMat);
    eyeL.position.set(-0.12 * scale, 0.48 * scale, 0.2 * scale);
    const eyeR = eyeL.clone();
    eyeR.position.x = 0.12 * scale;
    headGroup.add(head, snout, eyeL, eyeR);
    spine.add(headGroup);

    function makeLeg(side) {
      const hip = new THREE.Group();
      hip.position.set(side * 0.22 * scale, -0.02 * scale, 0);
      const thigh = new THREE.Mesh(capsuleGeo(0.11 * scale, 0.32 * scale, 3, 6), fur);
      thigh.position.y = -0.16 * scale;
      thigh.castShadow = true;
      const shinGroup = new THREE.Group();
      shinGroup.position.y = -0.32 * scale;
      const shin = new THREE.Mesh(capsuleGeo(0.1 * scale, 0.32 * scale, 3, 6), fur);
      shin.position.y = -0.16 * scale;
      shin.castShadow = true;
      const footGroup = new THREE.Group();
      footGroup.position.y = -0.32 * scale;
      const foot = new THREE.Mesh(new THREE.BoxGeometry(0.14 * scale, 0.06 * scale, 0.22 * scale), skin);
      foot.position.set(0, -0.03 * scale, 0.05 * scale);
      footGroup.add(foot);
      shinGroup.add(shin, footGroup);
      hip.add(thigh, shinGroup);
      return { hip, shinGroup, footGroup };
    }

    function makeArm(side) {
      const shoulder = new THREE.Group();
      shoulder.position.set(side * 0.48 * scale, 0.48 * scale, 0);
      shoulder.rotation.z = side * 0.35;
      const upper = new THREE.Mesh(capsuleGeo(0.1 * scale, 0.28 * scale, 3, 6), fur);
      upper.position.y = -0.14 * scale;
      upper.castShadow = true;
      const foreGroup = new THREE.Group();
      foreGroup.position.y = -0.28 * scale;
      const fore = new THREE.Mesh(capsuleGeo(0.09 * scale, 0.28 * scale, 3, 6), fur);
      fore.position.y = -0.14 * scale;
      fore.castShadow = true;
      foreGroup.add(fore);
      shoulder.add(upper, foreGroup);
      return { shoulder, foreGroup };
    }

    const leftLeg = makeLeg(-1);
    const rightLeg = makeLeg(1);
    pelvis.add(leftLeg.hip, rightLeg.hip);
    const leftArm = makeArm(-1);
    const rightArm = makeArm(1);
    spine.add(leftArm.shoulder, rightArm.shoulder);
    g.add(pelvis);

    g.userData.limbs = {
      pelvis,
      spine,
      torso,
      headGroup,
      head,
      legL: leftLeg.hip,
      shinL: leftLeg.shinGroup,
      footL: leftLeg.footGroup,
      legR: rightLeg.hip,
      shinR: rightLeg.shinGroup,
      footR: rightLeg.footGroup,
      armL: leftArm.shoulder,
      foreL: leftArm.foreGroup,
      armR: rightArm.shoulder,
      foreR: rightArm.foreGroup,
    };
    return g;
  }

  function makeFurnitureMesh(fu, world) {
    const q = resolveFuQ(fu, world);
    const p = to3(fu.x + fu.w / 2, fu.y + fu.h / 2);
    const w = fu.w * SCALE;
    const d = fu.h * SCALE;
    const g = new THREE.Group();
    g.userData.label = fu.label || fu.kind;
    g.userData.qualities = q;
    g.userData.kind = fu.kind;
    g.position.set(p.x, 0, p.z);

    if (fu.kind === "desk") {
      const woodMat = matFromQualities(q, FURN_COLORS.desk);
      const top = new THREE.Mesh(new THREE.BoxGeometry(w, 0.08, d), woodMat);
      top.position.y = 0.72;
      top.castShadow = true;
      const legGeo = new THREE.BoxGeometry(0.08, 0.72, 0.08);
      [[-1, -1], [-1, 1], [1, -1], [1, 1]].forEach(([sx, sz]) => {
        const leg = new THREE.Mesh(legGeo, stdMat(0x4e342e, 0.9));
        leg.position.set(sx * w * 0.42, 0.36, sz * d * 0.38);
        leg.castShadow = true;
        g.add(leg);
      });
      g.add(top);
      const monStand = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.18, 0.08), stdMat(0x37474f));
      monStand.position.set(0, 0.88, -d * 0.15);
      const screenOn = world.web && world.web.active;
      const screen = new THREE.Mesh(
        new THREE.BoxGeometry(w * 0.38, w * 0.22, 0.04),
        new THREE.MeshStandardMaterial({
          color: screenOn ? 0x1e88e5 : 0x111111,
          emissive: screenOn ? 0x1565c0 : 0x000000,
          emissiveIntensity: screenOn ? 0.65 : 0,
          roughness: 0.35,
        })
      );
      screen.position.set(0, 1.02, -d * 0.18);
      g.add(monStand, screen);
      return g;
    }

    if (fu.kind === "tv") {
      const stand = new THREE.Mesh(new THREE.BoxGeometry(w * 0.55, 0.12, d * 0.35), stdMat(0x37474f));
      stand.position.y = 0.35;
      const frame = new THREE.Mesh(new THREE.BoxGeometry(w, w * 0.58, 0.12), stdMat(0x1a1a1a, 0.5));
      frame.position.y = 0.95;
      const tvOn = world.tv && world.tv.active;
      const screen = new THREE.Mesh(
        new THREE.BoxGeometry(w * 0.88, w * 0.5, 0.02),
        new THREE.MeshStandardMaterial({
          color: tvOn ? 0x1565c0 : 0x050505,
          emissive: tvOn ? 0x0d47a1 : 0x000000,
          emissiveIntensity: tvOn ? 0.8 : 0,
          roughness: 0.25,
        })
      );
      screen.position.set(0, 0.95, 0.07);
      g.add(stand, frame, screen);
      return g;
    }

    if (fu.kind === "bed") {
      const base = new THREE.Mesh(new THREE.BoxGeometry(w, 0.28, d), matFromQualities(q, FURN_COLORS.bed));
      base.position.y = 0.28;
      const mattress = new THREE.Mesh(
        new THREE.BoxGeometry(w * 0.92, 0.18, d * 0.9),
        matFromQualities({ ...q, texture: "algodón", softness: 0.9 }, 0xe8eaf6)
      );
      mattress.position.y = 0.5;
      const pillow = new THREE.Mesh(
        new THREE.BoxGeometry(w * 0.28, 0.1, d * 0.35),
        matFromQualities({ ...q, texture: "algodón" }, 0xffffff)
      );
      pillow.position.set(w * 0.28, 0.62, -d * 0.22);
      g.add(base, mattress, pillow);
      return g;
    }

    if (fu.kind === "fridge") {
      const body = new THREE.Mesh(
        new THREE.BoxGeometry(w * 0.85, 1.35, d * 0.75),
        matFromQualities(q, FURN_COLORS.fridge)
      );
      body.position.y = 0.68;
      body.castShadow = true;
      const handle = new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.35, 0.04), stdMat(0x455a64));
      handle.position.set(w * 0.32, 0.75, d * 0.38);
      g.add(body, handle);
      return g;
    }

    if (fu.kind === "sofa") {
      const fabric = matFromQualities(q, FURN_COLORS.sofa);
      const seat = new THREE.Mesh(new THREE.BoxGeometry(w, 0.32, d * 0.85), fabric);
      seat.position.y = 0.38;
      const back = new THREE.Mesh(new THREE.BoxGeometry(w, 0.42, 0.14), fabric.clone());
      back.position.set(0, 0.68, -d * 0.36);
      const armL = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.28, d * 0.75), stdMat(0x8d6e63));
      armL.position.set(-w * 0.46, 0.48, 0);
      const armR = armL.clone();
      armR.position.x = w * 0.46;
      g.add(seat, back, armL, armR);
      return g;
    }

    if (fu.kind === "bath") {
      const tub = new THREE.Mesh(new THREE.BoxGeometry(w, 0.42, d), matFromQualities(q, FURN_COLORS.bath));
      tub.position.y = 0.32;
      const rim = new THREE.Mesh(
        new THREE.BoxGeometry(w * 1.02, 0.06, d * 1.02),
        matFromQualities({ ...q, texture: "porcelana" }, 0xffffff)
      );
      rim.position.y = 0.52;
      g.add(tub, rim);
      return g;
    }

    if (fu.kind === "toilet") {
      const base = new THREE.Mesh(new THREE.BoxGeometry(w * 0.7, 0.35, d * 0.65), stdMat(FURN_COLORS.toilet));
      base.position.y = 0.22;
      const tank = new THREE.Mesh(new THREE.BoxGeometry(w * 0.55, 0.38, 0.12), stdMat(0xeeeeee));
      tank.position.set(0, 0.55, -d * 0.28);
      g.add(base, tank);
      return g;
    }

    if (fu.kind === "stove") {
      const body = new THREE.Mesh(
        new THREE.BoxGeometry(w * 0.9, 0.88, d * 0.85),
        matFromQualities(q, FURN_COLORS.stove)
      );
      body.position.y = 0.44;
      body.castShadow = true;
      const top = new THREE.Mesh(new THREE.BoxGeometry(w * 0.92, 0.06, d * 0.88), matFromQualities(q, 0x263238));
      top.position.y = 0.9;
      const burnerMat = matFromQualities(
        { ...q, temperature_c: q.emissive ? 90 : 24, emissive: true },
        0x212121
      );
      burnerMat.emissive = new THREE.Color(0xbf360c);
      burnerMat.emissiveIntensity = q.emissive ? 0.85 : 0.15;
      [[-0.22, -0.18], [0.22, -0.18], [-0.22, 0.18], [0.22, 0.18]].forEach(([bx, bz]) => {
        const burner = new THREE.Mesh(new THREE.CylinderGeometry(w * 0.12, w * 0.12, 0.03, 12), burnerMat);
        burner.position.set(bx * w, 0.94, bz * d);
        g.add(burner);
      });
      g.add(body, top);
      return g;
    }

    const fallback = new THREE.Mesh(new THREE.BoxGeometry(w, 1.2, d), stdMat(FURN_COLORS[fu.kind] || 0x888888));
    fallback.position.y = 0.6;
    fallback.castShadow = true;
    g.add(fallback);
    return g;
  }

  function makeBookMesh(isArchetypeCard) {
    const g = new THREE.Group();
    const cover = new THREE.Mesh(
      new THREE.BoxGeometry(0.28, 0.38, 0.08),
      stdMat(isArchetypeCard ? 0x6a1b9a : 0x1565c0, 0.7)
    );
    cover.position.y = 0.22;
    cover.castShadow = true;
    const pages = new THREE.Mesh(new THREE.BoxGeometry(0.24, 0.34, 0.06), stdMat(0xfff8e1, 0.95));
    pages.position.set(0.01, 0.22, 0.01);
    g.add(cover, pages);
    return g;
  }

  function clearGroup(arr) {
    arr.forEach((m) => {
      scene.remove(m);
      m.traverse((c) => {
        if (c.geometry) c.geometry.dispose();
        if (c.material) {
          if (Array.isArray(c.material)) c.material.forEach((mat) => mat.dispose());
          else c.material.dispose();
        }
      });
    });
    arr.length = 0;
  }

  function worldSignature(world) {
    return JSON.stringify({
      furniture: world.furniture,
      objects: world.objects,
      trees: world.trees,
      tv: world.tv,
      web: world.web,
      pantry: world.pantry,
      room_temp: world.room_temp,
    });
  }

  function rebuildWorld(world) {
    if (!scene || !world) return;
    const sig = worldSignature(world);
    if (sig === worldSig) return;
    worldSig = sig;
    lastWorld = world;

    clearGroup(furnitureMeshes);
    clearGroup(objectMeshes);
    clearGroup(treeMeshes);

    (world.furniture || []).forEach((fu) => {
      if (fu.kind === "door") return;
      const mesh = makeFurnitureMesh(fu, world);
      mesh.traverse((c) => {
        if (c.isMesh) c.castShadow = true;
      });
      scene.add(mesh);
      furnitureMeshes.push(mesh);
    });

    (world.objects || []).forEach((obj) => {
      const p = to3(obj.x, obj.y);
      let m;
      if (obj.kind === "crop") {
        m = makeCropMesh(obj);
      } else {
        // Read alias: saved objects used meta.tarot.
        const isArchetypeCard = !!(obj.meta && (obj.meta.archetype_card || obj.meta.tarot));
        m = makeBookMesh(isArchetypeCard);
      }
      m.position.set(p.x, 0, p.z);
      m.userData.label = obj.label || (obj.kind === "crop" ? "cultivo" : "objeto");
      m.userData.qualities =
        obj.qualities ||
        (window.NexoMaterialQualities
          ? window.NexoMaterialQualities.resolveObjectQualities(obj)
          : null);
      m.traverse((c) => {
        if (c.isMesh) c.castShadow = true;
      });
      scene.add(m);
      objectMeshes.push(m);
    });

    (world.trees || []).forEach((t) => {
      const p = to3(t.x, t.y);
      const trunk = new THREE.Mesh(
        new THREE.CylinderGeometry(0.12, 0.18, 1.4, 8),
        stdMat(0x4e342e, 0.92)
      );
      trunk.position.set(p.x, 0.7, p.z);
      trunk.castShadow = true;
      const crown = new THREE.Mesh(
        new THREE.SphereGeometry(t.r * SCALE * 0.95, 10, 8),
        stdMat(0x2d5a27, 0.88)
      );
      crown.position.set(p.x, 1.95, p.z);
      crown.castShadow = true;
      const crown2 = crown.clone();
      crown2.scale.set(0.75, 0.65, 0.75);
      crown2.position.set(p.x + 0.15, 2.15, p.z + 0.1);
      scene.add(trunk, crown, crown2);
      treeMeshes.push(trunk, crown, crown2);
    });
  }

  function makeCropMesh(obj) {
    const meta = obj.meta || {};
    const ripe = meta.ripe !== false;
    const g = new THREE.Group();
    const soil = new THREE.Mesh(
      new THREE.CylinderGeometry(0.35, 0.38, 0.08, 10),
      stdMat(0x5d4037, 0.92)
    );
    soil.position.y = 0.04;
    const stem = new THREE.Mesh(
      new THREE.CylinderGeometry(0.03, 0.04, ripe ? 0.55 : 0.25, 6),
      stdMat(0x558b2f, 0.88)
    );
    stem.position.y = ripe ? 0.32 : 0.18;
    g.add(soil, stem);
    if (ripe) {
      const fruitColor = {
        tomate: 0xc62828,
        lechuga: 0x7cb342,
        zanahoria: 0xef6c00,
        fresa: 0xe53935,
        albahaca: 0x689f38,
        calabaza: 0xff8f00,
      }[meta.food] || 0x8bc34a;
      const fruit = new THREE.Mesh(new THREE.SphereGeometry(0.18, 8, 6), stdMat(fruitColor, 0.75));
      fruit.position.y = 0.62;
      fruit.scale.set(1, 0.85, 1);
      g.add(fruit);
    }
    return g;
  }

  function applyBiomechPose(mesh, bio, gait, walking) {
    const limbs = mesh.userData.limbs;
    if (!limbs || !bio) {
      animateLimbs(mesh, gait, walking);
      return;
    }
    const bones = bio.bones || {};
    const pelvis = bones.pelvis || {};
    const spine = bones.spine || {};
    const ragdoll = bio.ragdoll;

    if (limbs.pelvis) {
      limbs.pelvis.rotation.x = pelvis.pitch || 0;
      limbs.pelvis.rotation.z = pelvis.roll || 0;
    }
    if (limbs.spine) {
      limbs.spine.rotation.x = (spine.lumbar || 0) * 0.55 + (spine.thoracic || 0) * 0.35;
    }
    if (limbs.torso && !limbs.spine) {
      limbs.torso.rotation.x = (pelvis.pitch || 0) + (spine.lumbar ? spine.lumbar * 0.5 : 0);
      limbs.torso.rotation.z = pelvis.roll || 0;
    }
    const cerv = spine.cervical != null ? spine.cervical : 0;
    if (limbs.headGroup) {
      limbs.headGroup.rotation.x = cerv * 0.65;
      limbs.headGroup.rotation.y = walking ? Math.sin(gait * Math.PI * 2) * 0.06 : 0;
    } else if (limbs.head) {
      limbs.head.rotation.x = cerv * 0.6;
      limbs.head.rotation.y = walking ? Math.sin(gait * Math.PI * 2) * 0.06 : 0;
    }

    const hl = bones.hip_l && bones.hip_l.flex != null ? bones.hip_l.flex : 0;
    const hr = bones.hip_r && bones.hip_r.flex != null ? bones.hip_r.flex : 0;
    const kl = bones.knee_l && bones.knee_l.flex != null ? bones.knee_l.flex : 0;
    const kr = bones.knee_r && bones.knee_r.flex != null ? bones.knee_r.flex : 0;
    const al = bones.ankle_l && bones.ankle_l.flex != null ? bones.ankle_l.flex : 0;
    const ar = bones.ankle_r && bones.ankle_r.flex != null ? bones.ankle_r.flex : 0;
    const sl = bones.shoulder_l && bones.shoulder_l.flex != null ? bones.shoulder_l.flex : 0;
    const sr = bones.shoulder_r && bones.shoulder_r.flex != null ? bones.shoulder_r.flex : 0;
    const el = bones.elbow_l && bones.elbow_l.flex != null ? bones.elbow_l.flex : 0;
    const er = bones.elbow_r && bones.elbow_r.flex != null ? bones.elbow_r.flex : 0;

    if (limbs.legL) {
      limbs.legL.rotation.x = hl;
      limbs.legL.rotation.z = ragdoll ? 0.25 : 0;
    }
    if (limbs.shinL) limbs.shinL.rotation.x = kl;
    else if (limbs.legL) limbs.legL.rotation.x = hl + kl * 0.85;
    if (limbs.footL) limbs.footL.rotation.x = al;

    if (limbs.legR) {
      limbs.legR.rotation.x = hr;
      limbs.legR.rotation.z = ragdoll ? -0.25 : 0;
    }
    if (limbs.shinR) limbs.shinR.rotation.x = kr;
    else if (limbs.legR) limbs.legR.rotation.x = hr + kr * 0.85;
    if (limbs.footR) limbs.footR.rotation.x = ar;

    if (limbs.armL) {
      limbs.armL.rotation.x = sl;
      if (!limbs.foreL) limbs.armL.rotation.z = 0.35 + (ragdoll ? 0.4 : 0);
    }
    if (limbs.foreL) {
      limbs.foreL.rotation.x = el;
      limbs.armL.rotation.z = 0.35 + (ragdoll ? 0.4 : 0);
    }
    if (limbs.armR) {
      limbs.armR.rotation.x = sr;
      if (!limbs.foreR) limbs.armR.rotation.z = -0.35 - (ragdoll ? 0.4 : 0);
    }
    if (limbs.foreR) {
      limbs.foreR.rotation.x = er;
      limbs.armR.rotation.z = -0.35 - (ragdoll ? 0.4 : 0);
    }
  }

  function animateLimbs(mesh, gait, walking) {
    const limbs = mesh.userData.limbs;
    if (!limbs) return;
    const swing = walking ? Math.sin(gait * Math.PI * 2) * 0.55 : 0;
    if (limbs.armL) limbs.armL.rotation.x = swing;
    if (limbs.armR) limbs.armR.rotation.x = -swing;
    if (limbs.legL) limbs.legL.rotation.x = -swing * 0.85;
    if (limbs.legR) limbs.legR.rotation.x = swing * 0.85;
    if (limbs.torso) limbs.torso.rotation.x = walking ? Math.sin(gait * Math.PI * 2) * 0.04 : 0;
    if (limbs.head) limbs.head.rotation.y = walking ? Math.sin(gait * Math.PI * 2) * 0.08 : 0;
  }

  function placeAgent(mesh, x, y, dir, agentState) {
    const p = to3(x, y);
    const gait = agentState && agentState.gait_phase != null ? agentState.gait_phase : 0;
    const walking = agentState && agentState.walking;
    const bio = agentState && agentState.biomech;
    const heightM = bio && bio.height_m != null ? bio.height_m : 0;
    const bodyAngle = bio && bio.body_angle != null ? bio.body_angle : 0;
    const ragdoll = bio && bio.ragdoll;
    const runScale = bio && bio.gait === "run" ? 1.35 : 1.0;
    const bob = (walking ? Math.sin(gait * Math.PI * 2) * 0.14 * runScale : 0) + heightM * 2.2;
    const sway = walking ? Math.sin(gait * Math.PI * 2) * 0.05 : 0;
    mesh.position.set(p.x, bob, p.z);
    mesh.rotation.y = dir >= 0 ? -Math.PI / 2 : Math.PI / 2;
    mesh.rotation.z = sway + bodyAngle;
    mesh.rotation.x = ragdoll ? 0.55 + (bio && bio.bones && bio.bones.spine ? bio.bones.spine.thoracic * 0.3 : 0) : 0;
    applyBiomechPose(mesh, bio, gait, walking || (bio && (bio.gait === "run" || bio.gait === "walk" || bio.gait === "swim")));
  }

  function applyEnvironment(env) {
    if (!sunLight || !scene) return;
    const light = env && env.light_level != null ? env.light_level : 1;
    const phase = (env && env.phase) || "day";
    sunLight.intensity = 0.2 + light * 0.75;
    ambLight.intensity = 0.15 + light * 0.4;
    if (phase === "night") {
      scene.background = new THREE.Color(0x0a1628);
      scene.fog.color.set(0x0a1628);
    } else if (phase === "dusk") {
      scene.background = new THREE.Color(0x4a3728);
      scene.fog.color.set(0x4a3728);
    } else if (phase === "dawn") {
      scene.background = new THREE.Color(0x6a8caf);
      scene.fog.color.set(0x6a8caf);
    } else {
      scene.background = new THREE.Color(0x87ceeb);
      scene.fog.color.set(0x87ceeb);
    }
  }

  function updateGaze(agent, vision) {
    if (!gazeCone || !agent) return;
    const p = to3(agent.x, agent.y);
    gazeCone.position.set(p.x, 0.2, p.z);
    gazeCone.rotation.y = agent.dir >= 0 ? -Math.PI / 2 : Math.PI / 2;
    if (vision && vision.fixation) {
      gazeCone.material.opacity = 0.18;
    } else {
      gazeCone.material.opacity = 0.08;
    }
  }

  function renderFrame(state) {
    if (!initialized || !renderer || !scene || !camera) return;
    const { world, player, companion, offspring, env, vision } = state;
    rebuildWorld(world);
    placeAgent(agentMesh, player.x, player.y, player.dir, player);
    placeAgent(companionMesh, companion.x, companion.y, companion.dir || -1, companion);
    if (offspring) {
      offspringMesh.visible = true;
      placeAgent(offspringMesh, offspring.x, offspring.y, offspring.dir || 1, offspring);
    } else {
      offspringMesh.visible = false;
    }
    applyEnvironment(env);
    updateGaze(player, vision);
    updateCameraFocus(player.x, player.y);
    if (divineIntensity > 0.01) {
      setDivineVoice(divineIntensity * 0.92);
    }
    if (window.SkyVoice && camera) {
      const pp = to3(player.x, player.y);
      const p = camera.position;
      const t = new THREE.Vector3(pp.x, orbit.targetY, pp.z);
      const fwd = new THREE.Vector3().subVectors(t, p).normalize();
      window.SkyVoice.updateListener(p.x, p.y, p.z, fwd.x, fwd.y, fwd.z);
    }
    if (renderer) renderer.render(scene, camera);
  }

  function domElement() {
    return renderer ? renderer.domElement : null;
  }

  function setPickHandler(fn) {
    onPick = typeof fn === "function" ? fn : null;
  }

  window.NexoRenderer = {
    init,
    renderFrame,
    domElement,
    initialized: () => initialized,
    setPickHandler,
    pickAt,
    setDivineVoice,
    formatQualitiesLabel,
  };
})();
