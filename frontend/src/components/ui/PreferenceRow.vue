<template>
    <label class="pref-row" :for="forId">
        <slot name="label" />
        <slot />
    </label>
</template>

<script setup>
defineProps({
    forId: {
        type: String,
        required: true,
    },
});
</script>
