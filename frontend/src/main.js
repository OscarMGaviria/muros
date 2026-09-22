import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import VueKonva from 'vue-konva'
import Tres from '@tresjs/core'

const app = createApp(App)
app.use(VueKonva)
app.use(Tres)
app.mount('#app')
