<template>
    <header>
        <h1>Be Sure ance</h1>
        <h3>Choosing an insurance plan should be easy</h3>
        <h4>Made with ❤️ by <a href="https://gabrielongzm.com/">Gabriel Ong</a>. Source code <a href="https://github.com/gongahkia/be-sure-ance">here.</a></h4>
        <p>Last scraped on {{ lastMonday }} 00:00:00+08:00</p>
        <img src="https://github.com/gongahkia/be-sure-ance/actions/workflows/scrape-to-supabase.yml/badge.svg" alt="Workflow Status">
    </header>
</template>

<script>
export default {
    computed: {
        lastMonday() {
            const now = new Date();
            const day = now.getDay(); 
            const diff = (day === 1 ? 0 : day === 0 ? 6 : day - 1); 
            const lastMonday = new Date(now);
            lastMonday.setDate(now.getDate() - diff);
            lastMonday.setHours(0, 0, 0, 0); 
            return lastMonday.toISOString().split('T')[0]; 
        }
    }
};
</script>