import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import VueKonva from 'vue-konva'
import Tres from '@tresjs/core'
import { createPinia } from 'pinia'

const app = createApp(App)
app.use(createPinia())
app.use(VueKonva)
app.use(Tres)
app.mount('#app')

