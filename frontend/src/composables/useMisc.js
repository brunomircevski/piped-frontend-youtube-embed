import { getPreferenceBoolean, getPreferenceString } from "./usePreferences.js";
import { getAuthToken } from "./useApi.js";

// Logged-in users land on their subscription feed unless they picked a home page.
// Every reader must pass the same default: preference refs are cached per key.
export function defaultHomepage() {
    return getAuthToken() ? "feed" : "trending";
}

export function getHomepagePreference() {
    return getPreferenceString("homepage", defaultHomepage());
}

export async function updateWatched(videos) {
    if (window.db && getPreferenceBoolean("watchHistory", false)) {
        var tx = window.db.transaction("watch_history", "readonly");
        var store = tx.objectStore("watch_history");
        videos.map(async video => {
            var request = store.get(video.url.substr(-11));
            request.onsuccess = function (event) {
                if (event.target.result) {
                    video.watched = event.target.result.currentTime != 0;
                    video.currentTime = event.target.result.currentTime;
                }
            };
        });
    }
}

export function download(text, filename, mimeType) {
    var file = new Blob([text], { type: mimeType });

    const elem = document.createElement("a");

    elem.href = URL.createObjectURL(file);
    elem.download = filename;
    elem.click();
    elem.remove();
}

export function getHomePage() {
    switch (getHomepagePreference()) {
        case "trending":
            return "/trending";
        case "feed":
            return "/feed";
        default:
            return undefined;
    }
}
