/**
 * Cualidades físicas — espejo del backend (brain/material_qualities.py).
 */
(function (global) {
  const FURNITURE_BASE = {
    desk: { texture: "roble", material: "madera", temperature_c: 19.5, roughness: 0.82, metalness: 0.04, softness: 0.12, hardness: 0.78 },
    tv: { texture: "plástico mate", material: "electrónica", temperature_c: 22, roughness: 0.45, metalness: 0.12, softness: 0.05 },
    fridge: { texture: "acero cepillado", material: "metal", temperature_c: 8, roughness: 0.38, metalness: 0.72, softness: 0.02 },
    bed: { texture: "algodón", material: "textil", temperature_c: 21, roughness: 0.94, metalness: 0, softness: 0.88 },
    sofa: { texture: "terciopelo", material: "textil", temperature_c: 20.5, roughness: 0.91, metalness: 0, softness: 0.82 },
    bath: { texture: "porcelana", material: "cerámica", temperature_c: 18, roughness: 0.22, metalness: 0.08, softness: 0.08 },
    toilet: { texture: "porcelana sanitaria", material: "cerámica", temperature_c: 17.5, roughness: 0.28, metalness: 0.06 },
    stove: { texture: "hierro fundido", material: "metal", temperature_c: 24, roughness: 0.55, metalness: 0.65, softness: 0.01 },
    door: { texture: "madera pintada", material: "madera", temperature_c: 19, roughness: 0.75, metalness: 0.05 },
  };

  function merge(a, b) {
    return Object.assign({}, a, b);
  }

  function resolveFurnitureQualities(fu, world) {
    if (fu.qualities) return fu.qualities;
    const kind = fu.kind || "desk";
    const base = merge(FURNITURE_BASE[kind] || FURNITURE_BASE.desk, { kind });
    const roomTemp = (world && world.room_temp) != null ? world.room_temp : 20;
    base.ambient_c = roomTemp;
    const tvOn = world && world.tv && world.tv.active;
    const webOn = world && world.web && world.web.active;
    const stoveHot = world && world.pantry && world.pantry.some((p) => p && !p.raw);

    if (kind === "fridge") {
      base.temperature_c = 4;
      base.feels = "frío al tacto";
    } else if (kind === "stove" && stoveHot) {
      base.temperature_c = 85;
      base.feels = "caliente — precaución";
      base.emissive = true;
    } else if (kind === "tv" && tvOn) {
      base.temperature_c = 28;
      base.feels = "emite calor leve";
      base.emissive = true;
    } else if (kind === "desk" && webOn) {
      base.temperature_c = 24;
      base.feels = "pantalla activa";
      base.emissive = true;
    } else if (kind === "sofa") {
      base.temperature_c = roomTemp + 0.8;
      base.feels = "acogedor";
    } else if (kind === "bed") {
      base.feels = "suave y cálido";
    } else if (kind === "bath") {
      base.feels = "cerámica húmeda";
    } else {
      base.feels = defaultFeel(base);
    }
    return base;
  }

  function resolveObjectQualities(obj) {
    if (obj.qualities) return obj.qualities;
    const meta = obj.meta || {};
    if (obj.kind === "crop") {
      return {
        kind: "crop",
        texture: "orgánico",
        material: "vegetal",
        temperature_c: meta.ripe !== false ? 14 : 16,
        roughness: 0.85,
        softness: 0.55,
        feels: meta.ripe !== false ? "fresco del jardín" : "tierno",
        label_food: meta.food || "",
      };
    }
    // Read alias: saved objects used meta.tarot.
    if (meta.archetype_card || meta.tarot) {
      return {
        kind: "book",
        texture: "cartulina mate",
        material: "papel",
        temperature_c: 20,
        roughness: 0.72,
        feels: "misterioso al tacto",
      };
    }
    return {
      kind: "book",
      texture: "papel encuadernado",
      material: "papel",
      temperature_c: 20,
      roughness: 0.88,
      softness: 0.35,
      feels: "seco",
    };
  }

  function defaultFeel(q) {
    const t = q.temperature_c || 20;
    if (t < 10) return "frío";
    if (t > 35) return "caliente";
    if ((q.softness || 0) > 0.7) return "blando";
    if ((q.hardness || 0) > 0.8) return "duro";
    return "neutro";
  }

  function formatQualities(q) {
    if (!q) return "";
    const parts = [];
    if (q.texture) parts.push(q.texture);
    if (q.temperature_c != null) parts.push(q.temperature_c + "°C");
    if (q.feels) parts.push(q.feels);
    if (q.material) parts.push(q.material);
    return parts.join(" · ");
  }

  global.NexoMaterialQualities = {
    resolveFurnitureQualities,
    resolveObjectQualities,
    formatQualities,
    FURNITURE_BASE,
  };
})(window);
