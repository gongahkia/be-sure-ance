<template>
    <header>
        <h1><b>Be Sure</b> ance</h1>
        <h3>Made with ❤️ by <a href="https://gabrielongzm.com/">Gabriel Ong</a></h3>
        <h4>Source code <a href="https://github.com/gongahkia/be-sure-ance">here</a></h4>
        <p>Last scraped on {{ lastMonday }}</p>
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