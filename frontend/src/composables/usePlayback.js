// State shared by the YouTube embed and the audio-only player: remembered
// speed, per-video watch progress and SponsorBlock labels.

const STORAGE_SPEED_KEY = "playbackRate";
const STORAGE_PROGRESS_KEY = "watchProgress";
export const MIN_RATE = 0.25;
export const MAX_RATE = 2;
const MIN_SAVE_SECONDS = 10;
const MAX_PROGRESS_RATIO = 0.9;
const MAX_PROGRESS_ENTRIES = 500;

const CATEGORY_LABELS = {
    sponsor: "Sponsor",
    selfpromo: "Self-promotion",
    interaction: "Interaction reminder",
    intro: "Intro",
    outro: "Outro",
    preview: "Preview",
    music_offtopic: "Non-music section",
    filler: "Filler",
};

function readJSON(key) {
    try {
        const raw = localStorage.getItem(key);
        return raw ? JSON.parse(raw) : null;
    } catch {
        return null;
    }
}

function writeJSON(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
    } catch {
        /* ignore quota / disabled storage */
    }
}

export function readStoredSpeed() {
    try {
        const n = Number(localStorage.getItem(STORAGE_SPEED_KEY) ?? 1);
        return n >= MIN_RATE && n <= MAX_RATE ? n : 1;
    } catch {
        return 1;
    }
}

export function writeStoredSpeed(rate) {
    try {
        localStorage.setItem(STORAGE_SPEED_KEY, String(rate));
    } catch {
        /* ignore */
    }
}

function isRestorableProgress(time, total) {
    return total > 0 && time >= MIN_SAVE_SECONDS && time < total * MAX_PROGRESS_RATIO;
}

// Where to start a video: an explicit time (?t=, or a switch between players)
// wins, then saved progress.
export function getStartSeconds(videoId, explicitStart = 0) {
    if (explicitStart > 0) return Math.floor(explicitStart);
    const entry = (readJSON(STORAGE_PROGRESS_KEY) || {})[videoId];
    if (entry && isRestorableProgress(entry.currentTime, entry.duration)) return Math.floor(entry.currentTime);
    return 0;
}

export function saveWatchProgress(videoId, time, total) {
    if (!videoId || !(total > 0)) return;
    const all = readJSON(STORAGE_PROGRESS_KEY) || {};

    if (isRestorableProgress(time, total)) {
        all[videoId] = { currentTime: Math.floor(time), duration: Math.floor(total), updatedAt: Date.now() };
        const ids = Object.keys(all);
        if (ids.length > MAX_PROGRESS_ENTRIES) {
            ids.sort((a, b) => (all[a].updatedAt ?? 0) - (all[b].updatedAt ?? 0));
            ids.slice(0, ids.length - MAX_PROGRESS_ENTRIES).forEach(id => delete all[id]);
        }
    } else {
        delete all[videoId];
    }
    writeJSON(STORAGE_PROGRESS_KEY, all);
    updateHistoryDatabase(videoId, time);
}

// Keeps Piped's watch history (thumbnail progress bars) in sync, like the native player.
function updateHistoryDatabase(videoId, time) {
    if (!window.db) return;
    try {
        const store = window.db.transaction("watch_history", "readwrite").objectStore("watch_history");
        const request = store.get(videoId);
        request.onsuccess = event => {
            const entry = event.target.result;
            if (!entry) return;
            entry.currentTime = time;
            store.put(entry);
        };
    } catch {
        /* history disabled or db unavailable */
    }
}

export function categoryLabel(category) {
    return CATEGORY_LABELS[category] ?? category;
}
