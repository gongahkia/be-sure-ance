import { createApp } from 'vue'
import App from './App.vue'
import { initializeObservability } from './observability'

const app = createApp(App)
initializeObservability(app)
app.mount('#app')
