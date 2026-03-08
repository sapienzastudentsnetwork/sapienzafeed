'use strict';

const root = document.documentElement;

const THEME_KEY = 'theme';

/* ------------------------- color helpers ------------------------- */

const clamp01 = (x) => Math.min(1, Math.max(0, x));

function hexToRgb(hex) {
    const m = String(hex).trim().match(/^#?([0-9a-f]{6})$/i);
    if (!m) throw new Error(`Bad hex: ${hex}`);
    const n = parseInt(m[1], 16);
    return { r: (n >> 16) & 255, g: (n >> 8) & 255, b: n & 255 };
}

function rgbToHex({ r, g, b }) {
    const h = (v) => v.toString(16).padStart(2, '0');
    return `#${h(r)}${h(g)}${h(b)}`;
}

function mix(hexA, hexB, t) {
    t = clamp01(t);
    const a = hexToRgb(hexA), b = hexToRgb(hexB);
    return rgbToHex({
      r: Math.round(a.r + (b.r - a.r) * t),
      g: Math.round(a.g + (b.g - a.g) * t),
      b: Math.round(a.b + (b.b - a.b) * t),
    });
}

function rgbToHsl({ r, g, b }) {
    r /= 255; g /= 255; b /= 255;
    const max = Math.max(r, g, b), min = Math.min(r, g, b);
    const d = max - min;
    let h = 0, s = 0;
    const l = (max + min) / 2;

    if (d !== 0) {
      s = d / (1 - Math.abs(2 * l - 1));
      switch (max) {
        case r: h = ((g - b) / d) % 6; break;
        case g: h = (b - r) / d + 2; break;
        case b: h = (r - g) / d + 4; break;
      }
      h *= 60;
      if (h < 0) h += 360;
    }
    return { h, s, l };
}

function hslToRgb({ h, s, l }) {
    const c = (1 - Math.abs(2 * l - 1)) * s;
    const hp = ((h % 360) + 360) % 360 / 60;
    const x = c * (1 - Math.abs((hp % 2) - 1));
    let r1 = 0, g1 = 0, b1 = 0;

    if (hp >= 0 && hp < 1) [r1, g1, b1] = [c, x, 0];
    else if (hp < 2)      [r1, g1, b1] = [x, c, 0];
    else if (hp < 3)      [r1, g1, b1] = [0, c, x];
    else if (hp < 4)      [r1, g1, b1] = [0, x, c];
    else if (hp < 5)      [r1, g1, b1] = [x, 0, c];
    else                  [r1, g1, b1] = [c, 0, x];

    const m = l - c / 2;
    return {
      r: Math.round((r1 + m) * 255),
      g: Math.round((g1 + m) * 255),
      b: Math.round((b1 + m) * 255),
    };
}

function adjustLightness(hex, delta /* -1..+1 */) {
    const hsl = rgbToHsl(hexToRgb(hex));
    hsl.l = clamp01(hsl.l + delta);
    return rgbToHex(hslToRgb(hsl));
}

function relLuminance(hex) {
    const { r, g, b } = hexToRgb(hex);
    const lin = (v) => {
      v /= 255;
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    };
    const R = lin(r), G = lin(g), B = lin(b);
    return 0.2126 * R + 0.7152 * G + 0.0722 * B;
}

function contrastRatio(hexA, hexB) {
    const L1 = relLuminance(hexA);
    const L2 = relLuminance(hexB);
    const [hi, lo] = L1 >= L2 ? [L1, L2] : [L2, L1];
    return (hi + 0.05) / (lo + 0.05);
}

function bestTextOn(bgHex, preferredHex) {
    // Use preferred if it's decent; otherwise pick black/white.
    if (preferredHex && contrastRatio(bgHex, preferredHex) >= 4.5) return preferredHex;
    const black = '#000000', white = '#ffffff';
    return contrastRatio(bgHex, white) >= contrastRatio(bgHex, black) ? white : black;
}

/* ------------------------- theme application ------------------------- */

function applyPreset(name) {
    root.setAttribute('data-theme', name);
    root.removeAttribute('style'); // clears custom var overrides
}

function applyCustom(knobs) {
    root.setAttribute('data-theme', 'custom');
    const vars = computeVarsFromKnobs(knobs);
    for (const [k, v] of Object.entries(vars)) root.style.setProperty(k, v);
}

function computeVarsFromKnobs({ bg, fg, acc, but }) {
    // Decide whether to behave "light-ish" or "dark-ish" based on BG luminance.
    const isDarkBg = relLuminance(bg) < 0.35;

    // Inspired by your current light theme relationships:
    // - borders are subtle mixes of BG<->FG
    // - table header is a slightly distinct surface
    // - hover is a small step in the opposite direction of contrast
    const border = mix(bg, fg, isDarkBg ? 0.22 : 0.15);
    const softBorder = mix(border, bg, 0.35);
    const strongBorder = mix(border, fg, 0.20);

    const cardBgHover = isDarkBg ? adjustLightness(but, +0.04) : adjustLightness(but, +0.06);
    const linkHover = isDarkBg ? adjustLightness(acc, +0.06) : adjustLightness(acc, -0.08);

    const heading = mix(acc, fg, 0.20); // accent but pulled toward text for readability

    const tableHeaderBg = mix(but, bg, isDarkBg ? 0.25 : 0.35);
    const tableHeaderText = bestTextOn(tableHeaderBg, fg);

    const shadowColor = isDarkBg ? 'rgba(0, 0, 0, 0.5)' : 'rgba(0, 0, 0, 0.08)';

    return {
      '--bg-color': bg,
      '--text-color': fg,
      '--heading-color': heading,
      '--link-color': acc,
      '--link-hover-color': linkHover,

      '--toc-bg': but,
      '--card-bg': but,
      '--card-bg-hover': cardBgHover,

      '--border-color': border,
      '--toc-border': strongBorder,
      '--details-body-border': softBorder,
      '--card-border': softBorder,

      '--table-header-bg': tableHeaderBg,
      '--table-header-text': tableHeaderText,

      '--shadow-color': shadowColor,
    };
}

function saveState(state) {
    localStorage.setItem(THEME_KEY, JSON.stringify(state));
}

function loadState() {
    const raw = localStorage.getItem(THEME_KEY);
    if (!raw) return { mode: 'preset', name: 'auto' };
    try {
      return JSON.parse(raw);
    } catch {
      return { mode: 'preset', name: 'auto' };
    }
}

function applyState(state) {
    if (state?.mode === 'preset' && state?.name) {
      applyPreset(state.name);
      return;
    }
    if (state?.mode === 'custom' && state?.knobs) {
      applyCustom(state.knobs);
      return;
    }
    // fallback
    applyPreset('auto');
}

// Immediate execution (run in <head> to prevent flash)
(function() {

    applyState(loadState());

    // Prevent font flickering by applying it instantly to the HTML element
    const isFontDSA = localStorage.getItem('isFontDSA');
    if (isFontDSA) {
        document.documentElement.classList.add('dyslexic');
    }

})();

