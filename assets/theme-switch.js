'use strict';

/* ==========================================================================
   Theme Panel UI Initialization (Global Function)
   ========================================================================== */

window.initThemePanel = function() {
    const btn = document.getElementById('themeBtn');
    const panel = document.getElementById('themePanel');
    const backdrop = document.getElementById('panelBackdrop');

    // Prevent double initialization if called multiple times
    if (panel && panel.dataset.initialized) return;
    if (panel) panel.dataset.initialized = "true";

    const uiEls = {
        preset: document.getElementById('themePreset'),
        bg: document.getElementById('kBg'),
        srf: document.getElementById('kSrf'),
        fg: document.getElementById('kFg'),
        acc: document.getElementById('kAcc'),
        close: document.getElementById('closePanel'),
        reset: document.getElementById('resetCustomBtn'),
        exportBtn: document.getElementById('exportThemeBtn'),
        importInput: document.getElementById('importThemeInput'),
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
            const isCustom = state?.mode === 'custom';
            
            if (uiEls.preset) {
                uiEls.preset.value = isCustom ? 'custom' : (state?.name || 'auto');
            }

            const paletteTitle = document.getElementById('paletteTitle');
            if (paletteTitle) {
                const path = window.location.pathname.toLowerCase();
                let isItalian = false;

                // Force language based on URL path, fallback to browser language
                if (path.includes('/it/')) {
                    isItalian = true;
                } else if (path.includes('/en/')) {
                    isItalian = false;
                } else {
                    const userLang = navigator.language || navigator.userLanguage;
                    isItalian = userLang.toLowerCase().startsWith('it');
                }
                
                const textCustom = isItalian ? 'Palette personalizzata' : 'Custom Palette';
                const textActive = isItalian ? 'Palette attiva' : 'Active Palette';
                
                paletteTitle.textContent = isCustom ? textCustom : textActive;
            }

            if (uiEls.reset) {
                uiEls.reset.style.visibility = isCustom ? 'visible' : 'hidden';
            }

            const colorInputs = document.querySelectorAll('#themePanel .swatch__picker, #themePanel .swatch__hex');
            colorInputs.forEach(input => {
                input.disabled = !isCustom;
                input.style.opacity = isCustom ? '1' : '0.6'; 
                input.style.cursor = isCustom ? 'pointer' : 'not-allowed';
            });

            if (isCustom && state?.knobs) {
                if (uiEls.bg) { uiEls.bg.value = state.knobs.bg; document.getElementById('kBgHex').value = state.knobs.bg; }
                if (uiEls.fg) { uiEls.fg.value = state.knobs.fg; document.getElementById('kFgHex').value = state.knobs.fg; }
                if (uiEls.acc) { uiEls.acc.value = state.knobs.acc; document.getElementById('kAccHex').value = state.knobs.acc; }
                if (uiEls.srf) { uiEls.srf.value = state.knobs.srf; document.getElementById('kSrfHex').value = state.knobs.srf; }
            } else {
                setTimeout(() => {
                    const styles = getComputedStyle(document.documentElement);
                    
                    const getVar = (varName, fallback) => {
                        const val = styles.getPropertyValue(varName).trim();
                        return val.startsWith('#') ? val : fallback;
                    };

                    const currentBg = getVar('--bg-color', '#ffffff');
                    const currentSrf = getVar('--card-bg', '#f8f9fa');
                    const currentFg = getVar('--text-color', '#333333');
                    const currentAcc = getVar('--link-color', '#007BFF');

                    if (uiEls.bg) { uiEls.bg.value = currentBg; document.getElementById('kBgHex').value = currentBg; }
                    if (uiEls.srf) { uiEls.srf.value = currentSrf; document.getElementById('kSrfHex').value = currentSrf; }
                    if (uiEls.fg) { uiEls.fg.value = currentFg; document.getElementById('kFgHex').value = currentFg; }
                    if (uiEls.acc) { uiEls.acc.value = currentAcc; document.getElementById('kAccHex').value = currentAcc; }
                }, 50);
            }
        }

        // Apply initial UI state
        updateUI(loadState());

        // Event Listeners for Theme Panel
        if(btn) btn.addEventListener('click', () => setPanelOpen(true));
        if(uiEls.close) uiEls.close.addEventListener('click', () => setPanelOpen(false));
        if(backdrop) backdrop.addEventListener('click', () => setPanelOpen(false));

        if (uiEls.reset) {
            uiEls.reset.addEventListener('click', () => {
                const root = document.documentElement;
                
                // Backup current active styles
                const oldThemeAttr = root.getAttribute('data-theme');
                const oldCssText = root.style.cssText;
                
                // Clear inline vars and theme to force browser to compute default 'auto' CSS
                root.removeAttribute('data-theme');
                root.style.cssText = '';
                
                const styles = getComputedStyle(root);
                const getVar = (varName, fallback) => {
                    const val = styles.getPropertyValue(varName).trim();
                    return val.startsWith('#') ? val : fallback;
                };

                const autoKnobs = { 
                    bg: getVar('--bg-color', '#ffffff'), 
                    srf: getVar('--card-bg', '#f8f9fa'), 
                    fg: getVar('--text-color', '#333333'), 
                    acc: getVar('--link-color', '#007BFF') 
                };

                // Restore previous DOM state 
                if (oldThemeAttr) {
                    root.setAttribute('data-theme', oldThemeAttr);
                }
                root.style.cssText = oldCssText;

                const newState = { mode: 'custom', knobs: autoKnobs };
                saveState(newState);
                applyCurrentState(newState);
                updateUI(newState);
            });
        }

        /* ==========================================================================
           Import / Export Logic
           ========================================================================== */

        if (uiEls.exportBtn) {
            uiEls.exportBtn.addEventListener('click', () => {
                // Collect current values from the UI
                const exportData = {
                    bg: uiEls.bg.value,
                    srf: uiEls.srf.value,
                    fg: uiEls.fg.value,
                    acc: uiEls.acc.value
                };
                
                const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(exportData, null, 2));
                const downloadAnchorNode = document.createElement('a');
                downloadAnchorNode.setAttribute("href", dataStr);
                downloadAnchorNode.setAttribute("download", "sapienzafeed_theme.json");
                document.body.appendChild(downloadAnchorNode); // Required for Firefox
                downloadAnchorNode.click();
                downloadAnchorNode.remove();
            });
        }

        if (uiEls.importInput) {
            uiEls.importInput.addEventListener('change', (event) => {
                const file = event.target.files[0];
                if (!file) return;

                const reader = new FileReader();
                reader.onload = (e) => {
                    try {
                        const importedKnobs = JSON.parse(e.target.result);
                        
                        // Basic validation to ensure the file contains required color properties
                        if (importedKnobs.bg && importedKnobs.fg && importedKnobs.acc && importedKnobs.srf) {
                            const newState = { mode: 'custom', knobs: importedKnobs };
                            saveState(newState);
                            applyCurrentState(newState);
                            updateUI(newState);
                        } else {
                            alert("Invalid file format. Missing required color properties.");
                        }
                    } catch (err) {
                        alert("Error reading file. Ensure it is a valid JSON.");
                    }
                    // Reset the input to allow loading the same file again if needed
                    uiEls.importInput.value = ''; 
                };
                reader.readAsText(file);
            });
        }

        // Preset Dropdown Change
        uiEls.preset.addEventListener('change', (e) => {
            const val = e.target.value;
            const oldState = loadState() || {};
            let newState;
            
            if (val === 'custom') {
                if (oldState.knobs) {
                    newState = { mode: 'custom', knobs: oldState.knobs };
                } else {
                    // Read current values directly from the DOM to preserve 
                    // existing modifications or default base colors
                    newState = { 
                        mode: 'custom', 
                        knobs: {
                            bg: uiEls.bg.value,
                            srf: uiEls.srf.value,
                            fg: uiEls.fg.value,
                            acc: uiEls.acc.value
                        }
                    };
                }
            } else {
                newState = { mode: 'preset', name: val };
                if (oldState.knobs) {
                    newState.knobs = oldState.knobs;
                }
            }
            saveState(newState);
            applyCurrentState(newState);
            updateUI(newState);
        });

        // Input Listeners for Custom Colors
        const customInputs = [uiEls.bg, uiEls.fg, uiEls.acc, uiEls.srf];
        customInputs.forEach(input => {
            if(!input) return;
            input.addEventListener('input', () => {
                uiEls.preset.value = 'custom';
                const newState = {
                    mode: 'custom',
                    knobs: {
                        bg: uiEls.bg.value,
                        srf: uiEls.srf.value,
                        fg: uiEls.fg.value,
                        acc: uiEls.acc.value
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
            ["kSrf", "kSrfHex"],
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
};

/* ==========================================================================
   DOM Content Loaded Event
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {    
    // 1. OpenDyslexic Font Feature
    const fontElement = document.getElementById('font-dsa-toggle');
    if (fontElement) {
        const isFontDSA = localStorage.getItem("isFontDSA");
        if (isFontDSA) {
            fontElement.checked = true;
            document.documentElement.classList.add('dyslexic');
            
            // Wait for the browser to finish rendering the new font widths
            // before calculating the navbar layout on page load.
            if (typeof adjustNavbarLayout === 'function') {
                setTimeout(() => {
                    adjustNavbarLayout();
                }, 100); 
            }
        }

        fontElement.addEventListener('change', function() {
            if (this.checked) {
                document.documentElement.classList.add('dyslexic');
                localStorage.setItem("isFontDSA", "true");
            } else {
                document.documentElement.classList.remove('dyslexic');
                localStorage.removeItem("isFontDSA");
            }
            
            // Recalculate navbar layout as font width changes may trigger overflow
            if (typeof adjustNavbarLayout === 'function') {
                adjustNavbarLayout();
            }
        });
    }

    // 2. Initialize Theme Panel if natively present in HTML 
    // (This triggers on other pages where the panel is hardcoded)
    if (document.getElementById('themePanel')) {
        window.initThemePanel();
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
                    const bu = document.getElementById('kSrf'); if(bu) bu.value = newState.knobs.srf;
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