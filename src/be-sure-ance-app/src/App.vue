<template>
  <div id="app" :class="{ dark: isDark }">
    <ToggleButton :isDark="isDark" @toggle="toggleDark" />
    <Header />
    <div v-if="loading">Loading...</div>
    <div v-else>
      <SearchBar v-model="searchQuery" />
      <div class="card-container">
        <InsuranceCard
          title="AIA Singapore"
          link="https://www.aia.com.sg/en/index"
          :plans="filteredAiaPlans"
          :expanded="aiaExpanded"
          @toggle="toggleAiaExpanded"
        />
        <InsuranceCard
          title="China Life Singapore"
          link="https://www.chinalife.com.sg/"
          :plans="filteredChinaLifePlans"
          :expanded="chinaLifeExpanded"
          @toggle="toggleChinaLifeExpanded"
        />
        <InsuranceCard
          title="Chubb Insurance (Singapore)"
          link="https://www.chubb.com/sg-en/"
          :plans="filteredChubbPlans"
          :expanded="chubbExpanded"
          @toggle="toggleChubbExpanded"
        />
        <InsuranceCard
          title="United Overseas Insurance Limited (UOI)"
          link="https://www.uoi.com.sg/index.page"
          :plans="filteredUoiPlans"
          :expanded="uoiExpanded"
          @toggle="toggleUoiExpanded"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useDark, useToggle } from "@vueuse/core";
import { createClient } from '@supabase/supabase-js'

import ToggleButton from './components/ToggleButton.vue'
import Header from './components/AppHeader.vue'
import SearchBar from './components/SearchBar.vue'
import InsuranceCard from './components/InsuranceCard.vue'

const supabaseUrl = process.env.VUE_APP_SUPABASE_URL;
const supabaseKey = process.env.VUE_APP_SUPABASE_KEY;
const supabase = createClient(supabaseUrl, supabaseKey);

const isDark = useDark();
const toggleDark = useToggle(isDark);

const aiaPlans = ref([]);
const uoiPlans = ref([]);
const chinaLifePlans = ref([]);
const chubbPlans = ref([]);
const loading = ref(true);
const aiaExpanded = ref(false);
const uoiExpanded = ref(false);
const chinaLifeExpanded = ref(false);
const chubbExpanded = ref(false);
const searchQuery = ref("");

async function fetchData() {
  try {
    const { data: aiaData } = await supabase.from('aia').select('*');
    const { data: uoiData } = await supabase.from('uoi').select('*');
    const { data: chinaLifeData } = await supabase.from('china_life').select('*');
    const { data: chubbData } = await supabase.from('chubb').select('*');
    aiaPlans.value = aiaData;
    uoiPlans.value = uoiData;
    chinaLifePlans.value = chinaLifeData;
    chubbPlans.value = chubbData;
  } catch (error) {
    console.error('Error fetching data:', error);
  } finally {
    loading.value = false;
  }
}

fetchData();

function toggleAiaExpanded() {
  aiaExpanded.value = !aiaExpanded.value;
  uoiExpanded.value = false; 
  chinaLifeExpanded.value = false;
  chubbExpanded.value = false;
}

function toggleUoiExpanded() {
  uoiExpanded.value = !uoiExpanded.value;
  aiaExpanded.value = false; 
  chinaLifeExpanded.value = false;
  chubbExpanded.value = false;
}

function toggleChinaLifeExpanded() {
  chinaLifeExpanded.value = !chinaLifeExpanded.value;
  aiaExpanded.value = false; 
  uoiExpanded.value = false; 
  chubbExpanded.value = false;
}

function toggleChubbExpanded() {
  chubbExpanded.value = !chubbExpanded.value;
  aiaExpanded.value = false; 
  uoiExpanded.value = false; 
  chinaLifeExpanded.value = false;
}

const filteredAiaPlans = computed(() =>
  aiaPlans.value.filter(plan =>
    plan.plan_name.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
);

const filteredUoiPlans = computed(() =>
  uoiPlans.value.filter(plan =>
    plan.plan_name.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
);

const filteredChinaLifePlans = computed(() =>
  chinaLifePlans.value.filter(plan =>
    plan.plan_name.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
);

const filteredChubbPlans = computed(() =>
  chubbPlans.value.filter(plan =>
    plan.plan_name.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
);
</script>

<style scoped>
@import './assets/style.css';
</style>