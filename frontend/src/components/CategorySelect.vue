<script setup>
import { ref, computed, onMounted } from "vue";

const props = defineProps({
  modelValue: String,
  label: {
    type: String,
    default: "Заголовок",
  },
  categories: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(["update:modelValue", "select"]);

const open = ref(false);
const containerRef = ref(null);
const currentLabel = computed(() => {
  const selected = props.categories.find((cat) => cat.id === props.modelValue);
  return selected?.label || "Выбрать";
});

const selectCategory = (cat) => {
  emit("update:modelValue", cat.id);
  emit("select", cat);
  open.value = false;
};

import MdiSchool from "~icons/mdi/school";
import MdiHome from "~icons/mdi/home";
import MdiOfficeBuilding from "~icons/mdi/office-building";
import MdiLibraryBooks from "~icons/mdi/library-books";
import MdiFoodForkDrink from "~icons/mdi/food-fork-drink";
import MdiDumbbell from "~icons/mdi/dumbbell";
import MdiHospitalBox from "~icons/mdi/hospital-box";
import MdiWater from "~icons/mdi/water";
import MdiLightningBolt from "~icons/mdi/lightning-bolt";
import MdiFire from "~icons/mdi/fire";
import MdiBroom from "~icons/mdi/broom";
import MdiVolumeHigh from "~icons/mdi/volume-high";
import MdiWrench from "~icons/mdi/wrench";
import MdiSofa from "~icons/mdi/sofa";
import MdiWifi from "~icons/mdi/wifi";
import MdiCircleMedium  from "~icons/mdi/circle-medium";

const Icons = {
  "mdi-school": MdiSchool,
  "mdi-home": MdiHome,
  "mdi-office-building": MdiOfficeBuilding,
  "mdi-library-books": MdiLibraryBooks,
  "mdi-food-fork-drink": MdiFoodForkDrink,
  "mdi-dumbbell": MdiDumbbell,
  "mdi-hospital-box": MdiHospitalBox,
  "mdi-water": MdiWater,
  "mdi-lightning-bolt": MdiLightningBolt,
  "mdi-fire": MdiFire,
  "mdi-broom": MdiBroom,
  "mdi-volume-high": MdiVolumeHigh,
  "mdi-wrench": MdiWrench,
  "mdi-sofa": MdiSofa,
  "mdi-wifi": MdiWifi,
  "mdi-circle-medium": MdiCircleMedium,
};

onMounted(() => {
  document.addEventListener("click", (e) => {
    if (containerRef.value && !containerRef.value.contains(e.target)) open.value = false;
  });
});
</script>

<template>
  <div class="category-select" ref="containerRef" :aria-expanded="open">
    <label class="floating-label">{{ props.label }}</label>

    <button
      type="button"
      class="select-trigger"
      @click="open = !open"
      :aria-expanded="open"
      aria-haspopup="listbox"
    >
      <span class="placeholder">{{ currentLabel }}</span>
      <span class="arrow" :class="{ 'arrow-open': open }" aria-hidden="true"></span>
    </button>

    <transition name="dropdown">
      <ul v-if="open" class="dropdown" role="listbox" tabindex="-1">
        <li
          v-for="cat in props.categories"
          :key="cat.id"
          class="dropdown-item"
          role="option"
          @click="selectCategory(cat)"
        >
          <span class="icon" aria-hidden="true">
            <component :is="Icons[cat.icon] || Icons['mdi-circle-medium']" class="icon-svg" />
          </span>
          <span class="text">{{ cat.label }}</span>
        </li>
      </ul>
    </transition>
  </div>
</template>

<style scoped>
.category-select {
  position: relative;
  width: 100%;
  max-width: 320px;
  font-family: var(--font-text);
  box-sizing: border-box;
  margin-top: 20px;
}

.floating-label {
  position: absolute;
  top: -10px;
  left: 14px;
  background: #ffffff;
  padding: 0 8px;
  font-size: 14px;
  color: var(--color-font);
  pointer-events: none;
}

.select-trigger {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 18px 16px;
  border-radius: 20px;
  border: 1px solid var(--color-border);
  background: #ffffff;
  font-size: 18px;
  color: var(--color-font-option);
  cursor: pointer;
  box-sizing: border-box;
  transition: background 0.2s ease;
}

.select-trigger:hover {
  background: #fafafa;
}

.placeholder {
  text-align: left;
  flex: 1;
  color: var(--color-font);
  font-family: var(--font-text);
}

.arrow {
  width: 22px;
  height: 22px;
  position: relative;
  display: inline-block;
  flex: 0 0 18px;
  margin-left: 8px;
}
.arrow::before {
  content: "";
  position: absolute;
  width: 14px;
  height: 14px;
  left: -4px;
  border-left: 3px solid #666;
  border-bottom: 3px solid #666;
  border-radius: 1px;
  transform: rotate(-45deg);
  opacity: 1;
  transition: opacity 0.3s ease;
}
.arrow::after {
  content: "";
  position: absolute;
  top: 8px;
  left: -4px;
  width: 14px;
  height: 14px;
  border-left: 3px solid #666;
  border-top: 3px solid #666;
  border-radius: 1px;
  transform: rotate(45deg);
  opacity: 0;
  transition: opacity 0.3s ease;
}
.arrow-open::before {
  opacity: 0;
}
.arrow-open::after {
  opacity: 1;
}

.dropdown {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  width: 100%;
  background: #ffffff;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.06);
  padding: 8px;
  margin: 0;
  list-style: none;
  box-sizing: border-box;
  z-index: 40;
}

.dropdown-item {
  display: flex;
  align-items: center;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s ease;
  color: var(--color-font);
  user-select: none;
}

.icon {
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 28px;
  color: var(--color-font);
}

.icon-svg {
  width: 20px;
  height: 20px;
}

.text {
  width: fit-content;
  font-size: 16px;
  font-family: var(--font-text);
  padding: 6px;
  border-radius: 10px;
  border: 1px solid transparent;
  transition: background 0.2s ease, border-color 0.2s ease;
}

.dropdown-item:hover .text {
  background: var(--color-bg-option-selected);
  border-color: #b5bfba;
}

.dropdown-enter-active, .dropdown-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.dropdown-enter-from, .dropdown-leave-to {
  opacity: 0;
  transform: translateY(-10px) scale(0.95);
}

@media (min-width: 768px) {
  .category-select {
    width: 320px;
  }
  .select-trigger {
    padding: 20px 18px;
    font-size: 20px;
  }
}
</style>
