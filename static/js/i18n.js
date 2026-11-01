/**
 * EXPIRYGUARD AI — CLIENT-SIDE MULTILINGUAL TRANSLATION SYSTEM
 * Supports English ('en'), Hindi ('hi'), Marathi ('mr')
 */

let currentTranslations = {};
let allLanguagePacks = {};

async function initI18n() {
  try {
    const res = await fetch('/api/translations');
    const data = await res.json();
    currentTranslations = data.strings || {};
    allLanguagePacks = data.all_languages || {};
    
    // Set initial dropdown value
    const langSelect = document.getElementById('global-lang-select');
    if (langSelect && data.current_lang) {
      langSelect.value = data.current_lang;
    }
  } catch (err) {
    console.warn("Could not load translation pack:", err);
  }
}

function translateKey(key, defaultText = "") {
  if (currentTranslations && currentTranslations[key]) {
    return currentTranslations[key];
  }
  return defaultText || key;
}

async function changeLanguage(newLang) {
  try {
    const res = await fetch('/api/set-language', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lang: newLang })
    });
    const result = await res.json();
    if (result.success) {
      // Reload page to re-render all server-rendered templates in the chosen language
      window.location.reload();
    }
  } catch (err) {
    console.error("Language switch failed:", err);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  initI18n();
  
  const langSelect = document.getElementById('global-lang-select');
  if (langSelect) {
    langSelect.addEventListener('change', (e) => {
      changeLanguage(e.target.value);
    });
  }
});
