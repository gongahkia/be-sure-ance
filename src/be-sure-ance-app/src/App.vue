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
          title="Great Eastern Singapore"
          link="https://www.greateasternlife.com/sg/en/personal-insurance.html",
          :plans="filteredGreatEasternPlans"
          :expanded="greatEasternExpanded"
          @toggle="toggleGreatEasternExpanded"
        />

        <InsuranceCard
          title="HSBC Singapore Insurance"
          link="https://www.insurance.hsbc.com.sg/"
          :plans="filteredHsbcPlans"
          :expanded="hsbcExpanded"
          @toggle="toggleHsbcExpanded"
        />  

        <InsuranceCard
          title="India International Insurance (Singapore)"
          link="https://www.iii.com.sg/"
          :plans="filteredIiiPlans"
          :expanded="iiiExpanded"
          @toggle="toggleIiiExpanded"
        />

        <InsuranceCard
          title="Singlife"
          link="https://singlife.com/en"
          :plans="filteredSinglifePlans"
          :expanded="singlifeExpanded"
          @toggle="toggleSinglifeExpanded"
        />

        <InsuranceCard
          title="Sun Life"
          link="https://www.sunlife.com/en/"
          :plans="filteredSunlifePlans"
          :expanded="sunlifeExpanded"
          @toggle="toggleSunlifeExpanded"
        />

        <InsuranceCard
          title="Tokio Marine Insurance Group"
          link="https://www.tokiomarine.com/sg/en.html"
          :plans="filteredTokioMarinePlans"
          :expanded="tokioMarineExpanded"
          @toggle="toggleTokioMarineExpanded"
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
const loading = ref(true);
const searchQuery = ref("");

const aiaPlans = ref([]);
const uoiPlans = ref([]);
const chinaLifePlans = ref([]);
const chubbPlans = ref([]);
const tokioMarinePlans = ref([]);
const sunlifePlans = ref([]);
const singlifePlans = ref([]);
const greatEasternPlans = ref([]);
const hsbcPlans = ref([]);
const iiiPlans = ref([]);

const aiaExpanded = ref(false);
const uoiExpanded = ref(false);
const chinaLifeExpanded = ref(false);
const chubbExpanded = ref(false);
const tokioMarineExpanded = ref(false);
const sunlifeExpanded = ref(false);
const singlifeExpanded = ref(false);
const greatEasternExpanded = ref(false);
const hsbcExpanded = ref(false);
const iiiExpanded = ref(false);

async function fetchData() {
  try {

    const { data: aiaData } = await supabase.from('aia').select('*');
    const { data: uoiData } = await supabase.from('uoi').select('*');
    const { data: chinaLifeData } = await supabase.from('china_life').select('*');
    const { data: chubbData } = await supabase.from('chubb').select('*');
    const { data: tokioMarineData } = await supabase.from('tokio_marine').select('*');
    const { data: sunlifeData } = await supabase.from('sunlife').select('*');
    const { data: singlifeData } = await supabase.from('singlife').select('*');
    const { data: greatEasternData } = await supabase.from('great_eastern').select('*');
    const { data: hsbcData } = await supabase.from('hsbc').select('*');
    const { data: iiiData } = await supabase.from('iii').select('*');

    aiaPlans.value = aiaData;
    uoiPlans.value = uoiData;
    chinaLifePlans.value = chinaLifeData;
    chubbPlans.value = chubbData;
    tokioMarinePlans.value = tokioMarineData;
    sunlifePlans.value = sunlifeData;
    singlifePlans.value = singlifeData;
    greatEasternPlans.value = greatEasternData;
    hsbcPlans.value = hsbcData;
    iiiPlans.value = iiiData;

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
  tokioMarineExpanded.value = false;
  sunlifeExpanded.value = false;
  singlifeExpanded.value = false;
  greatEasternExpanded.value = false;
  hsbcExpanded.value = false;
  iiiExpanded.value = false;
}

function toggleUoiExpanded() {
  uoiExpanded.value = !uoiExpanded.value;
  aiaExpanded.value = false; 
  chinaLifeExpanded.value = false;
  chubbExpanded.value = false;
  tokioMarineExpanded.value = false;
  sunlifeExpanded.value = false;
  singlifeExpanded.value = false;
  greatEasternExpanded.value = false;
  hsbcExpanded.value = false;
  iiiExpanded.value = false;
}

function toggleChinaLifeExpanded() {
  chinaLifeExpanded.value = !chinaLifeExpanded.value;
  aiaExpanded.value = false; 
  uoiExpanded.value = false; 
  chubbExpanded.value = false;
  tokioMarineExpanded.value = false;
  sunlifeExpanded.value = false;
  singlifeExpanded.value = false;
  greatEasternExpanded.value = false;
  hsbcExpanded.value = false;
  iiiExpanded.value = false;
}

function toggleChubbExpanded() {
  chubbExpanded.value = !chubbExpanded.value;
  aiaExpanded.value = false; 
  uoiExpanded.value = false; 
  chinaLifeExpanded.value = false;
  tokioMarineExpanded.value = false;
  sunlifeExpanded.value = false;
  singlifeExpanded.value = false;
  greatEasternExpanded.value = false;
  hsbcExpanded.value = false;
  iiiExpanded.value = false;
}

function toggleTokioMarineExpanded() {
  tokioMarineExpanded.value = !tokioMarineExpanded.value;
  aiaExpanded.value = false; 
  uoiExpanded.value = false; 
  chinaLifeExpanded.value = false;
  chubbExpanded.value = false;
  sunlifeExpanded.value = false;
  singlifeExpanded.value = false;
  greatEasternExpanded.value = false;
  hsbcExpanded.value = false;
  iiiExpanded.value = false;
}

function toggleSunlifeExpanded() {
  sunlifeExpanded.value = !sunlifeExpanded.value;
  aiaExpanded.value = false; 
  uoiExpanded.value = false; 
  chinaLifeExpanded.value = false;
  chubbExpanded.value = false;
  tokioMarineExpanded.value = false;
  singlifeExpanded.value = false;
  greatEasternExpanded.value = false;
  hsbcExpanded.value = false;
  iiiExpanded.value = false;
}

function toggleSinglifeExpanded(){
  singlifeExpanded.value = !singlifeExpanded.value;
  aiaExpanded.value = false; 
  uoiExpanded.value = false; 
  chinaLifeExpanded.value = false;
  chubbExpanded.value = false;
  tokioMarineExpanded.value = false;
  sunlifeExpanded.value = false;
  greatEasternExpanded.value = false;
  hsbcExpanded.value = false;
  iiiExpanded.value = false;
}

function toggleGreatEasternExpanded(){
  greatEasternExpanded.value = !greatEasternExpanded.value;
  aiaExpanded.value = false; 
  uoiExpanded.value = false; 
  chinaLifeExpanded.value = false;
  chubbExpanded.value = false;
  tokioMarineExpanded.value = false;
  sunlifeExpanded.value = false;
  singlifeExpanded.value = false;
  hsbcExpanded.value = false;
  iiiExpanded.value = false;
}

function toggleHsbcExpanded(){
  hsbcExpanded.value = !hsbcExpanded.value;
  aiaExpanded.value = false; 
  uoiExpanded.value = false; 
  chinaLifeExpanded.value = false;
  chubbExpanded.value = false;
  tokioMarineExpanded.value = false;
  sunlifeExpanded.value = false;
  singlifeExpanded.value = false;
  greatEasternExpanded.value = false;
  iiiExpanded.value = false; 
}

function toggleIiiExpanded(){
  iiiExpanded.value = !iiiExpanded.value;
  aiaExpanded.value = false; 
  uoiExpanded.value = false; 
  chinaLifeExpanded.value = false;
  chubbExpanded.value = false;
  tokioMarineExpanded.value = false;
  sunlifeExpanded.value = false;
  singlifeExpanded.value = false;
  greatEasternExpanded.value = false;
  hsbcExpanded.value = false;
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

const filteredTokioMarinePlans = computed(() =>
  tokioMarinePlans.value.filter(plan =>
    plan.plan_name.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
);  

const filteredSunlifePlans = computed(() =>
  sunlifePlans.value.filter(plan =>
    plan.plan_name.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
);

const filteredSinglifePlans = computed(() =>
  singlifePlans.value.filter(plan =>
    plan.plan_name.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
);

const filteredGreatEasternPlans = computed(() =>
  greatEasternPlans.value.filter(plan =>
    plan.plan_name.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
);

const filteredHsbcPlans = computed(() =>
  hsbcPlans.value.filter(plan =>
    plan.plan_name.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
);

const filteredIiiPlans = computed(() =>
  iiiPlans.value.filter(plan =>
    plan.plan_name.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
);
</script>

<style scoped>
@import './assets/style.css';
</style>