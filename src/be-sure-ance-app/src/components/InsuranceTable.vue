<template>
<table v-if="plans.length >0">
<thead>
    <tr>
        <th>Name</th>
        <th>Description</th>
        <th>Benefits</th>
        <th>Overview</th>
        <th>Brochure</th>
    </tr>
    </thead>
        <tbody>
            <tr v-for="plan in plans" :key="plan.id">
            <td><a :href='plan.plan_url'>{{ plan.plan_name }}</a></td>
            <td>{{ plan.plan_description }}</td>
            <td>
                <ul>
                    <li v-for='benefit in plan.plan_benefits' :key='benefit'>{{ benefit }}</li>
                </ul>
            </td>
            <td>{{ plan.plan_overview }}</td>
            <td>
                <a :href='plan.product_brochure_url'>Brochure Link</a>
            </td>
        </tr>
        </tbody>
    </table>
    <div v-else>
    No results found.
    </div>
</template>

<script setup>
defineProps({ plans:Array })
</script>