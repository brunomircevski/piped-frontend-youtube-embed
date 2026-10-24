<template>
    <CheckboxRoot
        :id="id"
        :model-value="modelValue"
        :disabled="disabled"
        :class="[
            'inline-flex size-4.5 shrink-0 cursor-pointer items-center justify-center rounded-[5px] border border-neutral-400 bg-transparent text-white disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:border-(--accent) data-[state=checked]:bg-(--accent) dark:border-neutral-500',
            customClass,
        ]"
        @update:model-value="handleUpdate"
    >
        <CheckboxIndicator class="inline-flex items-center justify-center text-current">
            <i-fa6-solid-check class="size-3" />
        </CheckboxIndicator>
    </CheckboxRoot>
</template>

<script setup>
import { CheckboxRoot, CheckboxIndicator } from "reka-ui";

defineOptions({
    name: "UiCheckbox",
});

defineProps({
    id: {
        type: String,
        default: undefined,
    },
    modelValue: {
        type: Boolean,
        default: false,
    },
    disabled: {
        type: Boolean,
        default: false,
    },
    customClass: {
        type: String,
        default: "",
    },
});

const emit = defineEmits(["update:modelValue", "change"]);

function handleUpdate(value) {
    const nextValue = value === true;
    emit("update:modelValue", nextValue);
    emit("change", nextValue);
}
</script>
