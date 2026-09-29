<script setup>
// Campo numérico ligado a store.params[field], con unidad, referencia normativa,
// ayuda y el error de validación del campo. Recalcula al confirmar el valor.
import { computed } from 'vue'
import { useWallStore } from '../../stores/wallStore'

const props = defineProps({
  field: { type: String, required: true },
  label: { type: String, required: true },
  unit: { type: String, default: '' },
  step: { type: [String, Number], default: '0.01' },
  min: { type: [String, Number], default: null },
  hint: { type: String, default: '' },
  norm: { type: String, default: '' },
  optional: { type: Boolean, default: false },
  placeholder: { type: String, default: '' }
})

const store = useWallStore()
const error = computed(() => store.fieldErrors[props.field])
const id = computed(() => `f-${props.field}`)

const value = computed({
  get: () => store.params[props.field],
  set: (v) => {
    // Un campo opcional vacío se guarda como null (p. ej. qn del estudio geotécnico)
    store.params[props.field] = (props.optional && (v === '' || v === null)) ? null : v
  }
})
</script>

<template>
  <div class="space-y-1">
    <label :for="id" class="flex items-baseline justify-between gap-2 text-xs font-medium text-slate-600">
      <span>{{ label }}</span>
      <span v-if="norm" class="text-[11px] font-normal text-slate-400">{{ norm }}</span>
    </label>
    <div class="flex rounded-md border bg-white overflow-hidden focus-within:ring-2"
         :class="error ? 'border-red-400 focus-within:ring-red-200' : 'border-slate-300 focus-within:ring-blue-200 focus-within:border-blue-500'">
      <input :id="id" type="number" :step="step" :min="min" v-model.number="value" @change="store.calculate()"
             :placeholder="placeholder" :aria-invalid="!!error" :aria-describedby="error ? id + '-err' : undefined"
             class="w-full min-w-0 px-2.5 py-1.5 text-sm font-mono tabular-nums text-slate-800 outline-none bg-transparent" />
      <span v-if="unit" class="shrink-0 px-2.5 py-1.5 text-xs text-slate-500 bg-slate-50 border-l border-slate-200">{{ unit }}</span>
    </div>
    <p v-if="error" :id="id + '-err'" class="text-xs text-red-600">{{ error }}</p>
    <p v-else-if="hint" class="text-[11px] leading-snug text-slate-400">{{ hint }}</p>
  </div>
</template>
