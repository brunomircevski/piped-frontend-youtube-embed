<template>
    <button
        :type="type"
        :class="['btn', variant === 'primary' ? '' : 'ring-1 ring-(--border) btn-ghost ring-inset', customClass]"
        v-bind="$attrs"
    >
        <slot />
    </button>
</template>

<script setup>
defineOptions({
    name: "UiButton",
});

defineProps({
    type: {
        type: String,
        default: "button",
        validator: val => ["button", "submit"].includes(val),
    },
    variant: {
        type: String,
        default: "primary",
        validator: val => ["primary", "secondary"].includes(val),
    },
    customClass: {
        type: String,
        default: "",
    },
});
</script>
