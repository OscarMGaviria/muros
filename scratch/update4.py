import os
file_path = r'frontend/src/components/ParametersForm.vue'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update imports
if "nextTick" not in content:
    content = content.replace("import { ref, watch, computed } from 'vue'", "import { ref, watch, computed, nextTick } from 'vue'")

# 2. Add watcher
watcher_code = """
const showKaModal = ref(false)

watch(showKaModal, async (newVal) => {
  if (newVal) {
    await nextTick()
    if (window.MathJax) {
      window.MathJax.typesetPromise()
    }
  }
})
"""
if "watch(showKaModal" not in content:
    content = content.replace("const showKaModal = ref(false)", watcher_code)

# 3. Replace text formula with MathJax LaTeX
old_formula = """          <div class="text-center py-2 text-xs font-mono text-slate-700 bg-white border border-orange-200 rounded px-2">
            Ka = sin²(θ+ϕ) / [sin²(θ)·sin(θ-δ)·(1+√x)²]
          </div>
          <p class="text-[10px] text-slate-500 mt-2 text-center">Donde x = [sin(ϕ+δ)·sin(ϕ-β)] / [sin(θ-δ)·sin(θ+β)]</p>"""

new_formula = """          <div class="text-center py-2 text-sm text-slate-800 bg-white border border-orange-200 rounded px-2 overflow-x-auto custom-scrollbar">
            $$ K_a = \\frac{\\sin^2(\\theta + \\phi)}{\\sin^2\\theta \\sin(\\theta - \\delta) \\left[ 1 + \\sqrt{\\frac{\\sin(\\phi + \\delta) \\sin(\\phi - \\beta)}{\\sin(\\theta - \\delta) \\sin(\\theta + \\beta)}} \\right]^2 } $$
          </div>"""

content = content.replace(old_formula, new_formula)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated successfully")
