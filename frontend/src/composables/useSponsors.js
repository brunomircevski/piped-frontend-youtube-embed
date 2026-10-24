import { fetchJson, apiUrl } from "./useApi.js";
import { getPreferenceBoolean, getPreferenceJSON, getPreferenceNumber, getPreferenceString } from "./usePreferences.js";

// SponsorBlock segments for a video, filtered by the user's skip preferences.
// Resolves to null when SponsorBlock is disabled or the request fails.
export async function fetchSponsors(videoId) {
    if (!getPreferenceBoolean("sponsorblock", true)) return null;

    let selectedSkip = getPreferenceString("selectedSkip", "sponsor,interaction,selfpromo,music_offtopic").split(",");
    const skipOptions = getPreferenceJSON("skipOptions");
    if (skipOptions !== undefined) {
        selectedSkip = Object.keys(skipOptions).filter(k => skipOptions[k] !== undefined && skipOptions[k] !== "no");
    }

    const sponsorsData = await fetchJson(apiUrl() + "/sponsors/" + videoId, {
        category: JSON.stringify(selectedSkip),
    }).catch(() => null);
    if (!sponsorsData) return null;

    sponsorsData.segments?.forEach(segment => {
        const option = skipOptions?.[segment.category];
        segment.autoskip = option === undefined || option === "auto";
    });

    const minSegmentLength = Math.max(getPreferenceNumber("minSegmentLength", 0), 0);
    sponsorsData.segments = sponsorsData.segments?.filter(segment => {
        const length = segment.segment[1] - segment.segment[0];
        return length >= minSegmentLength;
    });

    return sponsorsData;
}
