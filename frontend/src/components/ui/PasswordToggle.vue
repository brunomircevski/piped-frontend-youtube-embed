<template>
    <button
        type="button"
        class="absolute right-1 btn size-8 min-h-8 btn-icon text-muted btn-ghost"
        :aria-label="modelValue ? $t('actions.hide_password') : $t('actions.show_password')"
        :aria-pressed="modelValue"
        @click="$emit('update:modelValue', !modelValue)"
    >
        <i-fa6-solid-eye v-if="!modelValue" />
        <i-fa6-solid-eye-slash v-else />
    </button>
</template>

<script setup>
import { useI18n } from "vue-i18n";

defineProps({
    modelValue: {
        type: Boolean,
        required: true,
    },
});

defineEmits(["update:modelValue"]);

const { t: $t } = useI18n();
</script>
