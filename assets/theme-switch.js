'use strict';

/* ==========================================================================
   Theme Panel UI Initialization
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
    const btn = document.getElementById('themeBtn');
    const panel = document.getElementById('themePanel');
    const backdrop = document.getElementById('panelBackdrop');

    const uiEls = {
        preset: document.getElementById('themePreset'),
        bg: document.getElementById('kBg'),
        fg: document.getElementById('kFg'),
        acc: document.getElementById('kAcc'),
        but: document.getElementById('kBut'),
        close: document.getElementById('closePanel'),
    };

    /**
     * Toggles the Theme Configuration Panel visibility.
     * @param {boolean} isOpen 
     */
    function setPanelOpen(isOpen) {
        if (!panel || !btn || !backdrop) return;
        panel.classList.toggle('is-open', isOpen);
        backdrop.hidden = !isOpen;
        panel.setAttribute('aria-hidden', String(!isOpen));
        btn.setAttribute('aria-expanded', String(isOpen));
    }

    // Initialize custom theme UI if available on the current page
    if (uiEls.preset && uiEls.close) {
        
        function updateUI(state) {
            if (state?.mode === 'preset' && state?.name) {
                uiEls.preset.value = state.name;
            } else if (state?.mode === 'custom' && state?.knobs) {
                uiEls.preset.value = 'custom';
                uiEls.bg.value = state.knobs.bg;
                uiEls.fg.value = state.knobs.fg;
                uiEls.acc.value = state.knobs.acc;
                uiEls.but.value = state.knobs.but;
            }
        }

        // Apply initial UI state
        updateUI(loadState());

        // Event Listeners for Theme Panel
        if(btn) btn.addEventListener('click', () => setPanelOpen(true));
        if(uiEls.close) uiEls.close.addEventListener('click', () => setPanelOpen(false));
        if(backdrop) backdrop.addEventListener('click', () => setPanelOpen(false));

        // Preset Dropdown Change
        uiEls.preset.addEventListener('change', (e) => {
            const val = e.target.value;
            let newState;
            if (val === 'custom') {
                // Read current values directly from the DOM to preserve 
                // existing modifications or default Dark base colors
                newState = { 
                    mode: 'custom', 
                    knobs: {
                        bg: uiEls.bg.value,
                        fg: uiEls.fg.value,
                        acc: uiEls.acc.value,
                        but: uiEls.but.value
                    }
                };
            } else {
                newState = { mode: 'preset', name: val };
            }
            saveState(newState);
            applyCurrentState(newState);
            updateUI(newState);
        });

        // Input Listeners for Custom Colors
        const customInputs = [uiEls.bg, uiEls.fg, uiEls.acc, uiEls.but];
        customInputs.forEach(input => {
            if(!input) return;
            input.addEventListener('input', () => {
                uiEls.preset.value = 'custom';
                const newState = {
                    mode: 'custom',
                    knobs: {
                        bg: uiEls.bg.value,
                        fg: uiEls.fg.value,
                        acc: uiEls.acc.value,
                        but: uiEls.but.value
                    }
                };
                saveState(newState);
                applyCurrentState(newState);
            });
        });

        // Handle hex inputs if they exist (sync text inputs to color pickers)
        const hexPairs = [
            ["kBg", "kBgHex"],
            ["kFg", "kFgHex"],
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

        for (const [pickerId, hexId] of hexPairs) {
            const picker = document.getElementById(pickerId);
            const hex = document.getElementById(hexId);
            if (!picker || !hex) continue;

            hex.value = picker.value;

            picker.addEventListener("input", () => {
                hex.value = picker.value;
                hex.classList.remove("is-bad");
            });

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
    }

    /* ==========================================================================
       OpenDyslexic Font Feature
       ========================================================================== */
       
    const fontElement = document.getElementById('font-dsa-toggle');
    if (fontElement) {
        const isFontDSA = localStorage.getItem("isFontDSA");
        if (isFontDSA) {
            fontElement.checked = true;
            document.documentElement.classList.add('dyslexic');
        }

        fontElement.addEventListener('change', function() {
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

/* ==========================================================================
   Cross-Tab Synchronization
   ========================================================================== */

window.addEventListener('storage', (event) => {
    if (event.key === THEME_KEY) {
        try {
            const newState = JSON.parse(event.newValue);
            applyCurrentState(newState);
            
            const presetSel = document.getElementById('themePreset');
            if(presetSel) {
                if (newState.mode === 'preset') {
                    presetSel.value = newState.name;
                } else if (newState.mode === 'custom' && newState.knobs) {
                    presetSel.value = 'custom';
                    const b = document.getElementById('kBg'); if(b) b.value = newState.knobs.bg;
                    const f = document.getElementById('kFg'); if(f) f.value = newState.knobs.fg;
                    const a = document.getElementById('kAcc'); if(a) a.value = newState.knobs.acc;
                    const bu = document.getElementById('kBut'); if(bu) bu.value = newState.knobs.but;
                }
            }
        } catch(e) {}
    } 
    else if (event.key === 'isFontDSA') {
        const isDSA = !!event.newValue;
        document.documentElement.classList.toggle('dyslexic', isDSA);
        const fontElement = document.getElementById('font-dsa-toggle');
        if (fontElement) fontElement.checked = isDSA;
    }
});

(function() {
    if (localStorage.getItem('isFontDSA')) {
        document.documentElement.classList.add('dyslexic');
    }
})();