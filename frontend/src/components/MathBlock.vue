<script setup>
// Renderiza una expresión LaTeX con MathJax en un elemento que Vue no administra,
// para que las actualizaciones de Vue y las de MathJax no se pisen.
import { onMounted, ref, watch } from 'vue'

const props = defineProps({
  tex: { type: String, required: true },
  text: { type: String, default: '' }  // versión legible si MathJax no está disponible
})
const el = ref(null)

async function render () {
  if (!el.value) return
  const mj = window.MathJax
  if (mj?.tex2chtmlPromise) {
    try {
      await mj.startup?.promise
      const node = await mj.tex2chtmlPromise(props.tex, { display: true })
      el.value.replaceChildren(node)
      mj.startup.document.clear()
      mj.startup.document.updateDocument()
      return
    } catch (err) {
      console.log('MathJax error: ', err)
    }
  }
  el.value.textContent = props.text || props.tex  // MathJax no disponible
}

onMounted(render)
watch(() => props.tex, render)
</script>

<template>
  <div ref="el" class="overflow-x-auto text-sm font-mono"></div>
</template>
