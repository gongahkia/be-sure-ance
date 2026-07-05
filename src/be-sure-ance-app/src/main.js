import { createApp } from 'vue'
import App from './App.vue'
import './assets/style.css'
import { initializeObservability } from './observability'

const app = createApp(App)
initializeObservability(app)
app.mount('#app')
