<template>
    <button
        type="button"
        class="absolute right-3 flex size-5 cursor-pointer items-center justify-center rounded-full bg-(--surface-hover) text-[10px] text-muted hover:text-(--text)"
        :aria-label="$t('actions.clear')"
        @click="$emit('clear')"
    >
        ⨉
    </button>
</template>

<script setup>
import { useI18n } from "vue-i18n";

defineEmits(["clear"]);

const { t: $t } = useI18n();
</script>
