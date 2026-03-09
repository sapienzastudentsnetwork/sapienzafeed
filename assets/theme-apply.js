'use strict';

const root = document.documentElement;
const THEME_KEY = 'theme';

/* ==========================================================================
   Color Manipulation Helpers
   ========================================================================== */

/**
 * Clamps a number between 0 and 1.
 * @param {number} x - The value to clamp.
 * @returns {number} The clamped value.
 */
const clamp01 = (x) => Math.min(1, Math.max(0, x));

/**
 * Converts a HEX color string to an RGB object.
 * @param {string} hex - The hex color (e.g., "#1a1a1a" or "1a1a1a").
 * @returns {Object} { r, g, b } representation.
 */
function hexToRgb(hex) {
    const match = String(hex).trim().match(/^#?([0-9a-f]{6})$/i);
    if (!match) throw new Error(`Invalid hex color: ${hex}`);
    const n = parseInt(match[1], 16);
    return { r: (n >> 16) & 255, g: (n >> 8) & 255, b: n & 255 };
}

/**
 * Converts an RGB object to a HEX color string.
 * @param {Object} rgb - { r, g, b } object.
 * @returns {string} Hexadecimal color string.
 */
function rgbToHex({ r, g, b }) {
    const toHex = (v) => v.toString(16).padStart(2, '0');
    return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

/**
 * Mixes two hex colors together based on a ratio.
 * @param {string} hexA - The base color.
 * @param {string} hexB - The color to mix in.
 * @param {number} t - The mixing ratio (0 to 1).
 * @returns {string} The resulting mixed hex color.
 */
function mix(hexA, hexB, t) {
    t = clamp01(t);
    const a = hexToRgb(hexA);
    const b = hexToRgb(hexB);
    return rgbToHex({
      r: Math.round(a.r + (b.r - a.r) * t),
      g: Math.round(a.g + (b.g - a.g) * t),
      b: Math.round(a.b + (b.b - a.b) * t),
    });
}

/**
 * Converts an RGB object to an HSL object.
 * @param {Object} rgb - { r, g, b } object.
 * @returns {Object} { h, s, l } representation.
 */
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

/**
 * Converts an HSL object to an RGB object.
 * @param {Object} hsl - { h, s, l } object.
 * @returns {Object} { r, g, b } representation.
 */
function hslToRgb({ h, s, l }) {
    const c = (1 - Math.abs(2 * l - 1)) * s;
    const hp = ((h % 360) + 360) % 360 / 60;
    const x = c * (1 - Math.abs((hp % 2) - 1));
    let r1 = 0, g1 = 0, b1 = 0;

    if (hp >= 0 && hp < 1) [r1, g1, b1] = [c, x, 0];
    else if (hp < 2)       [r1, g1, b1] = [x, c, 0];
    else if (hp < 3)       [r1, g1, b1] = [0, c, x];
    else if (hp < 4)       [r1, g1, b1] = [0, x, c];
    else if (hp < 5)       [r1, g1, b1] = [x, 0, c];
    else                   [r1, g1, b1] = [c, 0, x];

    const m = l - c / 2;
    return {
      r: Math.round((r1 + m) * 255),
      g: Math.round((g1 + m) * 255),
      b: Math.round((b1 + m) * 255),
    };
}

/* ==========================================================================
   Accessibility & Contrast Helpers (WCAG Guidelines)
   ========================================================================== */

/**
 * Adjusts the lightness of a hex color safely.
 * @param {string} hex - The base hex color.
 * @param {number} delta - The lightness adjustment (-1 to 1).
 * @returns {string} The adjusted hex color.
 */
function adjustLightness(hex, delta) {
    const hsl = rgbToHsl(hexToRgb(hex));
    hsl.l = clamp01(hsl.l + delta);
    return rgbToHex(hslToRgb(hsl));
}

/**
 * Calculates the WCAG relative luminance of a color.
 * @param {string} hex - The hex color.
 * @returns {number} The relative luminance value (0 to 1).
 */
function relLuminance(hex) {
    const { r, g, b } = hexToRgb(hex);
    const lin = (v) => {
        v /= 255;
        return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    };
    const R = lin(r), G = lin(g), B = lin(b);
    return 0.2126 * R + 0.7152 * G + 0.0722 * B;
}

/**
 * Calculates the WCAG contrast ratio between two colors.
 * @param {string} hexA - The first hex color.
 * @param {string} hexB - The second hex color.
 * @returns {number} The contrast ratio (1 to 21).
 */
function contrastRatio(hexA, hexB) {
    const L1 = relLuminance(hexA);
    const L2 = relLuminance(hexB);
    const [hi, lo] = L1 >= L2 ? [L1, L2] : [L2, L1];
    return (hi + 0.05) / (lo + 0.05);
}

/**
 * Determines the best text color (black, white, or preferred) for a given background.
 * @param {string} bgHex - The background color.
 * @param {string} preferredHex - The preferred text color to use if contrast is sufficient.
 * @returns {string} The chosen text hex color.
 */
function bestTextOn(bgHex, preferredHex) {
    // Use preferred if it passes WCAG AA for normal text (ratio >= 4.5)
    if (preferredHex && contrastRatio(bgHex, preferredHex) >= 4.5) return preferredHex;
    
    // Otherwise, calculate whether pure white or pure black provides better contrast
    const black = '#000000', white = '#ffffff';
    return contrastRatio(bgHex, white) >= contrastRatio(bgHex, black) ? white : black;
}

/* ==========================================================================
   State Management & Theme Engine
   ========================================================================== */

/**
 * Saves the current theme state to LocalStorage.
 * @param {Object} state - The theme configuration object.
 */
function saveState(state) {
    localStorage.setItem(THEME_KEY, JSON.stringify(state));
}

/**
 * Retrieves the theme state from LocalStorage.
 * @returns {Object} The parsed state or the default auto preset.
 */
function loadState() {
    const raw = localStorage.getItem(THEME_KEY);
    if (!raw) return { mode: 'preset', name: 'auto' };
    try {
        return JSON.parse(raw);
    } catch {
        return { mode: 'preset', name: 'auto' };
    }
}

/**
 * Applies a specific preset (auto, light, dark).
 * @param {string} name - The preset name.
 */
function applyPreset(name) {
    root.setAttribute('data-theme', name);
    // Remove inline custom variables to let CSS variables take over
    root.style.cssText = ''; 
}

/**
 * Computes the mathematical relationships between user-chosen colors
 * ensuring WCAG accessibility standards are met.
 * @param {Object} knobs - The base colors chosen by the user {bg, fg, acc, srf}.
 * @returns {Object} A dictionary of CSS variable mappings.
 */
function computeVarsFromKnobs({ bg, fg, acc, srf }) {
    // Decide whether to behave "light-ish" or "dark-ish" based on true visual luminance.
    const isDarkBg = relLuminance(bg) < 0.35;

    const border = mix(bg, fg, isDarkBg ? 0.22 : 0.15);
    const softBorder = mix(border, bg, 0.35);
    const strongBorder = mix(border, fg, 0.20);

    const cardBgHover = isDarkBg ? adjustLightness(srf, +0.04) : adjustLightness(srf, +0.06);
    const linkHover = isDarkBg ? adjustLightness(acc, +0.06) : adjustLightness(acc, -0.08);

    // Subtle pull towards the foreground color to prevent headings from burning eyes,
    // while maintaining strong accent identity
    const heading = mix(acc, fg, 0.20); 

    // Ensure links remain accessible on dark backgrounds
    const safeLink = isDarkBg ? mix(acc, fg, 0.15) : acc;

    const tableHeaderBg = mix(srf, bg, isDarkBg ? 0.25 : 0.35);
    // Programmatically ensure text inside the table header is readable
    const tableHeaderText = bestTextOn(tableHeaderBg, fg);

    const shadowColor = isDarkBg ? 'rgba(0, 0, 0, 0.5)' : 'rgba(0, 0, 0, 0.08)';

    return {
        '--bg-color': bg,
        '--text-color': fg,
        '--heading-color': heading,
        '--link-color': safeLink,
        '--link-hover-color': linkHover,
        '--toc-bg': srf,
        '--card-bg': srf,
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

/**
 * Computes and applies a custom theme generated from user-picked colors.
 * @param {Object} knobs - The base colors chosen by the user {bg, fg, acc, srf}.
 */
function applyCustom(knobs) {
    root.setAttribute('data-theme', 'custom');
    
    // Leverage the WCAG math engine to derive the rest of the palette
    const vars = computeVarsFromKnobs(knobs);
    
    let cssStr = '';
    for (const [k, v] of Object.entries(vars)) {
        cssStr += `${k}: ${v}; `;
    }
    root.style.cssText = cssStr;
}

/**
 * Main function to evaluate and apply the active state.
 * @param {Object} state 
 */
function applyCurrentState(state) {
    if (state?.mode === 'preset' && state?.name) {
        applyPreset(state.name);
    } else if (state?.mode === 'custom' && state?.knobs) {
        applyCustom(state.knobs);
    }
}

// Immediate execution (run in <head> to prevent style flash)
(function() {
    const state = loadState();
    applyCurrentState(state);
})();