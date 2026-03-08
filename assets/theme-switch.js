'use strict';

const btn = document.getElementById('themeBtn');
const panel = document.getElementById('themePanel');
const backdrop = document.getElementById('panelBackdrop');

const DEFAULT_CUSTOM_KNOBS = {
    bg:   '#1a1a1a',
    fg:   '#e0e0e0',
    acc:  '#66b2ff',
    but: '#252526',
};

function setOpen(open){
    panel.classList.toggle('is-open', open);
    backdrop.hidden = !open;
    panel.setAttribute('aria-hidden', String(!open));
    btn.setAttribute('aria-expanded', String(open));
}

//const root = document.documentElement;

const els = {
    preset: document.getElementById('themePreset'),
    bg: document.getElementById('kBg'),
    fg: document.getElementById('kFg'),
    acc: document.getElementById('kAcc'),
    but: document.getElementById('kBut'),
    close: document.getElementById('closePanel'),
};

// Only run the custom theme code if the panel UI is present on this page
if (els.preset && els.bg && els.fg && els.acc && els.but && els.close) {

    function applyState(state) {
        if (state?.mode === 'preset' && state?.name) {
          els.preset.value = state.name;
          applyPreset(state.name);
          return;
        }
        if (state?.mode === 'custom' && state?.knobs) {
          els.preset.value = 'custom';
          els.bg.value = state.knobs.bg;
          els.fg.value = state.knobs.fg;
          els.acc.value = state.knobs.acc;
          els.but.value = state.knobs.but;
          applyCustom(state.knobs);
          return;
        }
        // fallback
        els.preset.value = 'auto';
        applyPreset('auto');
    }

    function readKnobsFromInputs() {
      const knobs = {
        bg: els.bg?.value,
        fg: els.fg?.value,
        acc: els.acc?.value,
        but: els.but?.value,
      };

      // If any are missing/empty, treat as "not present"
      const ok = knobs.bg && knobs.fg && knobs.acc && knobs.but;
      return ok ? knobs : null;
    }

    /* ------------------------- events ------------------------- */

    btn.addEventListener('click', () => setOpen(!panel.classList.contains('is-open')));
    backdrop.addEventListener('click', () => setOpen(false));
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') setOpen(false); });
    els.close.addEventListener('click', () => setOpen(false));

    els.preset.addEventListener('change', () => {
      const v = els.preset.value;

      if (v === 'custom') {
        // Prefer current UI knobs; otherwise initialize to a dark-ish default
        const knobs = readKnobsFromInputs() ?? DEFAULT_CUSTOM_KNOBS;

        // Ensure the pickers show what we're applying
        els.bg.value = knobs.bg;
        els.fg.value = knobs.fg;
        els.acc.value = knobs.acc;
        els.but.value = knobs.but;

        applyCustom(knobs);
        saveState({ mode: 'custom', knobs });
        return;
      }

      applyPreset(v);
      saveState({ mode: 'preset', name: v });
    });

    // Optional: live preview as knobs change (comment out if you want "Save" only)
    for (const el of [els.bg, els.fg, els.acc, els.but]) {
        el.addEventListener('input', () => {
          const knobs = { bg: els.bg.value, fg: els.fg.value, acc: els.acc.value, but: els.but.value };
          els.preset.value = 'custom';
          applyCustom(knobs);
        });
    }

    // Settings and Preferences Listeners
    document.addEventListener("DOMContentLoaded", () => {
        // DSA Font Checkbox Initialization
        let fontElement = document.getElementById('font-dsa-toggle');
        if (fontElement) {
            let isFontDSA = localStorage.getItem("isFontDSA");
            if (isFontDSA) {
                fontElement.checked = true;
            }

            fontElement.addEventListener('change', function(e) {
                if (this.checked) {
                    document.documentElement.classList.add('dyslexic');
                    localStorage.setItem("isFontDSA", "true");
                } else {
                    document.documentElement.classList.remove('dyslexic');
                    localStorage.removeItem("isFontDSA");
                }
            });
        }
    });

    // Sync across tabs
    window.addEventListener('storage', (event) => {
        if (event.key === 'theme') {
            applyState(loadState());
        } else if (event.key === 'isFontDSA') {
            const isDSA = !!event.newValue;
            if (isDSA) document.documentElement.classList.add('dyslexic');
            else document.documentElement.classList.remove('dyslexic');
            const fontElement = document.getElementById('font-dsa-toggle');
            if (fontElement) fontElement.checked = isDSA;
        }
    });

    (() => {
      const pairs = [
        ["kBg",  "kBgHex"],
        ["kFg",  "kFgHex"],
        ["kAcc", "kAccHex"],
        ["kBut", "kButHex"],
      ];

      const normHex = (v) => {
        if (!v) return null;
        v = v.trim();
        if (!v.startsWith("#")) v = "#" + v;
        if (!/^#[0-9a-fA-F]{6}$/.test(v)) return null;
        return v.toLowerCase();
      };

      for (const [pickerId, hexId] of pairs) {
        const picker = document.getElementById(pickerId);
        const hex = document.getElementById(hexId);
        if (!picker || !hex) continue;

        // init
        hex.value = picker.value;

        // picker -> text
        picker.addEventListener("input", () => {
          hex.value = picker.value;
          hex.classList.remove("is-bad");
        });

        // text -> picker (on commit)
        const commit = () => {
          const v = normHex(hex.value);
          if (!v) {
            hex.classList.add("is-bad");
            return;
          }
          hex.classList.remove("is-bad");
          picker.value = v;
          picker.dispatchEvent(new Event("input", { bubbles: true }));
          picker.dispatchEvent(new Event("change", { bubbles: true }));
        };

        hex.addEventListener("change", commit);
        hex.addEventListener("keydown", (e) => {
          if (e.key === "Enter") commit();
        });
      }
    })();

    /* ------------------------- boot ------------------------- */

    // Page is fully loaded now
    // We load the state again so that also the values in the color pickers are synced
    applyState(loadState());
}