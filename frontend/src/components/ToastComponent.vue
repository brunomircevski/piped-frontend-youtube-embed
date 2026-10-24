<template>
    <div
        class="fixed right-4 bottom-4 z-9999 flex min-w-max items-center gap-4 rounded-2xl border border-(--border) bg-(--surface-raised) py-3 pr-3 pl-5 text-sm shadow-(--shadow) duration-200"
    >
        <slot />
        <button v-t="'actions.dismiss'" class="btn" @click="dismiss" />
    </div>
</template>

<script setup>
const emit = defineEmits(["dismissed"]);

function dismiss() {
    emit("dismissed");
}
</script>
