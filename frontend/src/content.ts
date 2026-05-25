/** Notifies the side panel when the user navigates to another video. */
function getVideoId(): string | null {
  return new URLSearchParams(window.location.search).get("v");
}

let lastVideoId = getVideoId();

const observer = new MutationObserver(() => {
  const current = getVideoId();
  if (current && current !== lastVideoId) {
    lastVideoId = current;
    chrome.runtime.sendMessage({ type: "VIDEO_CHANGED", videoId: current }).catch(() => {});
  }
});

observer.observe(document.querySelector("ytd-app") || document.body, {
  childList: true,
  subtree: true,
});

window.addEventListener("yt-navigate-finish", () => {
  const current = getVideoId();
  if (current && current !== lastVideoId) {
    lastVideoId = current;
    chrome.runtime.sendMessage({ type: "VIDEO_CHANGED", videoId: current }).catch(() => {});
  }
});
