<template>

  <div id="app" :class="{ dark: isDark }">
    <div class="toggle-button" @click="toggleDark()">
      {{ isDark ? '🌞' : '🌚' }}
    </div>

    <h1><b>Be Sure</b> ance</h1>
    <h3>Made with ❤️ by <a href="https://gabrielongzm.com/">Gabriel Ong</a></h3>
    <h4>Source code <a href="https://github.com/gongahkia/be-sure-ance">here</a></h4>

    <div v-if="loading">Loading...</div>
    <div v-else>

      <div class="card-container">
        <div class="card" @click="toggleAiaExpanded">
          <div class="card-header">
            <span><a href="https://www.aia.com.sg/en/index">AIA Singapore</a></span>
          </div>
          <Transition name="expand">
            <div class="card-content" v-show="aiaExpanded">
              <table>
                <thead>
                  <tr>
                    <th>Plan Name</th>
                    <th>Plan Description</th>
                    <th>Plan Benefits</th>
                    <th>Plan Overview</th>
                    <th>Product Brochure</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="plan in aiaPlans" :key="plan.id">
                    <td><a :href="plan.plan_url">{{ plan.plan_name }}</a></td>
                    <td>{{ plan.plan_description }}</td>
                    <td>
                      <ul>
                        <li v-for="benefit in plan.plan_benefits" :key="benefit">{{ benefit }}</li>
                      </ul>
                    </td>
                    <td>{{ plan.plan_overview }}</td>
                    <td><a :href="plan.product_brochure_url">{{ plan.product_brochure_url }}</a></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </Transition>
        </div>

        <div class="card" @click="toggleUoiExpanded">
          <div class="card-header">
            <span><a href="https://www.uoi.com.sg/index.page">United Overseas Insurance Limited (UOI)</a></span>
          </div>
          <Transition name="expand">
            <div class="card-content" v-show="uoiExpanded">
              <table>
                <thead>
                  <tr>
                    <th>Plan Name</th>
                    <th>Plan Description</th>
                    <th>Plan Benefits</th>
                    <th>Plan Overview</th>
                    <th>Product Brochure</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="plan in uoiPlans" :key="plan.id">
                    <td><a :href="plan.plan_url">{{ plan.plan_name }}</a></td>
                    <td>{{ plan.plan_description }}</td>
                    <td>
                      <ul>
                        <li v-for="benefit in plan.plan_benefits" :key="benefit">{{ benefit }}</li>
                      </ul>
                    </td>
                    <td>{{ plan.plan_overview }}</td>
                    <td><a :href="plan.product_brochure_url">{{ plan.product_brochure_url }}</a></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </Transition>
        </div>
      </div>
    </div>
    <button @click="toggleDark()">Toggle Mode</button>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useDark, useToggle } from "@vueuse/core";
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.VUE_APP_SUPABASE_URL;
const supabaseKey = process.env.VUE_APP_SUPABASE_KEY;
const supabase = createClient(supabaseUrl, supabaseKey);

const isDark = useDark();
const toggleDark = useToggle(isDark);

const aiaPlans = ref([]);
const uoiPlans = ref([]);
const loading = ref(true);
const aiaExpanded = ref(false);
const uoiExpanded = ref(false);

async function fetchData() {
  try {
    const { data: aiaData } = await supabase.from('aia').select('*');
    const { data: uoiData } = await supabase.from('uoi').select('*');
    aiaPlans.value = aiaData;
    uoiPlans.value = uoiData;
  } catch (error) {
    console.error('Error fetching data:', error);
  } finally {
    loading.value = false;
  }
}

function toggleAiaExpanded() {
  aiaExpanded.value = !aiaExpanded.value;
  uoiExpanded.value = false; // Close UOI card when AIA is opened
}

function toggleUoiExpanded() {
  uoiExpanded.value = !uoiExpanded.value;
  aiaExpanded.value = false; // Close AIA card when UOI is opened
}

fetchData();
</script>

<style scoped>
#app {
  font-family: Arial, sans-serif;
  text-align: center;
  transition: background-color 0.3s ease;
}

#app.dark {
  background-color: #16171d;
  color: #fff;
}

.card-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 20px;
}

.card {
  width: 80%;
  background-color: #f0f0f0;
  padding: 10px;
  border: 1px solid #ddd;
  cursor: pointer;
  margin-bottom: 10px;
}

#app.dark .card {
  background-color: #333;
  color: #fff;
}

.card-header {
  background-color: #ddd;
  padding: 10px;
  text-align: center;
}

#app.dark .card-header {
  background-color: #444;
  color: #fff;
}

.card-content {
  padding: 10px;
}

table {
  margin: 0 auto;
  border-collapse: collapse;
  width: 100%;
}

th, td {
  border: 1px solid #ddd;
  padding: 10px;
  text-align: left;
}

th {
  background-color: #f0f0f0;
}

#app.dark th {
  background-color: #333;
  color: #fff;
}

#app.dark td {
  background-color: #222;
  color: #fff;
}

.expand-enter-active,
.expand-leave-active {
  transition: all 0.5s ease;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  transform: scaleY(0);
}

.expand-enter-to,
.expand-leave-from {
  opacity: 1;
  transform: scaleY(1);
}

#app a {
  color: inherit;
}

#app.dark a {
  color: inherit;
}

.toggle-button {
  position: fixed;
  top: 10px;
  right: 10px;
  background-color: #f0f0f0;
  padding: 10px;
  border-radius: 5px;
  cursor: pointer;
  z-index: 1000;
}

#app.dark .toggle-button {
  background-color: #333;
  color: #fff;
}

.toggle-button:hover {
  background-color: #ddd;
}

#app.dark .toggle-button:hover {
  background-color: #444;
}
</style>