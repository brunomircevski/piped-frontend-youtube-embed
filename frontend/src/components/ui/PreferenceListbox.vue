<template>
    <ListboxRoot
        :id="id"
        :model-value="modelValue"
        multiple
        class="w-52 rounded-xl border border-(--border) bg-(--surface)"
        @update:model-value="handleUpdate"
    >
        <ListboxContent class="max-h-28 overflow-y-auto rounded-md p-1">
            <ListboxItem
                v-for="option in options"
                :key="option.value"
                :value="option.value"
                class="flex cursor-pointer items-center justify-between rounded-sm px-2 py-1 text-sm transition-colors outline-none data-highlighted:bg-(--surface-muted) data-[state=checked]:font-medium"
            >
                <span v-text="option.label" />
                <ListboxItemIndicator class="ml-2 text-(--accent)">✓</ListboxItemIndicator>
            </ListboxItem>
        </ListboxContent>
    </ListboxRoot>
</template>

<script setup>
import { ListboxContent, ListboxItem, ListboxItemIndicator, ListboxRoot } from "reka-ui";

defineProps({
    id: {
        type: String,
        required: true,
    },
    modelValue: {
        type: Array,
        required: true,
    },
    options: {
        type: Array,
        required: true,
    },
});

const emit = defineEmits(["update:modelValue", "change"]);

function handleUpdate(value) {
    emit("update:modelValue", value);
    emit("change", value);
}
</script>
