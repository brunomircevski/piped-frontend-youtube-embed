<script setup>
import { getPreferenceBoolean } from "@/composables/usePreferences.js";

defineProps({
    link: {
        type: String,
        required: true,
    },
    platform: {
        type: String,
        required: false,
        default: "YouTube",
    },
});
</script>

<template>
    <a v-if="getPreferenceBoolean('showWatchOnYouTube', false)" :href="link" class="btn shrink-0">
        <i-fa6-brands-youtube v-if="platform == 'YouTube'" />
        <i-fa6-brands-odysee v-else-if="platform == 'Odysee'" />
        <i18n-t keypath="player.watch_on" tag="span" class="max-lg:hidden">{{ platform }}</i18n-t>
    </a>
</template>
