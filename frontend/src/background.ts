chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => {});

chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (changeInfo.status !== "complete" || !tab.url?.includes("youtube.com/watch")) {
    return;
  }
  try {
    await chrome.sidePanel.setOptions({ tabId, path: "sidepanel.html", enabled: true });
  } catch {
    // Side panel may not be available on all builds
  }
});

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === "GET_ACTIVE_VIDEO") {
    chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
      const tab = tabs[0];
      if (!tab?.id || !tab.url?.includes("youtube.com/watch")) {
        sendResponse({ ok: false, error: "not_youtube" });
        return;
      }
      try {
        const [{ result }] = await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          func: () => {
            const params = new URLSearchParams(window.location.search);
            const videoId = params.get("v");
            const title =
              document.querySelector<HTMLMetaElement>('meta[name="title"]')?.content ||
              document.querySelector("h1.ytd-watch-metadata yt-formatted-string")?.textContent?.trim() ||
              document.title.replace(" - YouTube", "").trim();
            return { videoId, title, url: window.location.href };
          },
        });
        sendResponse({ ok: true, ...result });
      } catch {
        sendResponse({ ok: false, error: "script_failed" });
      }
    });
    return true;
  }
});
