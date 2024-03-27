// Persistent settings across multiple devices / sessions
// ------------------------------------------------------
(function () {
  // Visit /profile?edit=1 to change your settings, then update them here.
  const settings = {
    defaultPanel: '"lovelace"',
    dockedSidebar: '"docked"',
    enableShortcuts: "true",
    hiddenTabs: "{}",
    selectedLanguage: "null",
    selectedTheme: '{"dark":true}',
    sidebarHiddenPanels: '[]',
    sidebarPanelOrder:
      '["lovelace","hacs","logbook", "..."]',
    suspendWhenHidden: "true",
    vibrate: "true",
  };
  let settingsUpdated = false;
  const currentSettings = {};
  Object.keys(settings).forEach((key) => {
    currentSettings[key] = localStorage.getItem(key);
    if (currentSettings[key] !== settings[key]) {
      localStorage.setItem(key, settings[key]);
      settingsUpdated = true;
    }
  });
  const urlSearchParams = new URLSearchParams(location.search);
  if (!settingsUpdated) {
    console.log("Settings are up to date.");
    return;
  }
  if (urlSearchParams.get("edit") === "1") {
    console.warn(
      "Settings updated:\n",
      JSON.stringify(currentSettings, null, 2)
    );
  } else {
    console.warn("Settings updated, reloading page...");
    location.reload();
  }
})();
