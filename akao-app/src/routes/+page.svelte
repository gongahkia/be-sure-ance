<script lang="ts">
  import { onMount } from 'svelte';
  import '../app.css';
  import RouteTable from '$lib/components/RouteTable.svelte';
  import { normalizeRoute } from '$lib/utils/routes';

  type RouteRecord = ReturnType<typeof normalizeRoute>;

  let routes: RouteRecord[] = [];
  let loading = true;
  let error = '';

  onMount(async () => {
    try {
      const response = await fetch('/routes.json', {
        headers: {
          accept: 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Unable to load routes (${response.status})`);
      }

      const payload = await response.json();
      routes = Array.isArray(payload) ? payload.map(normalizeRoute) : [];
    } catch (err) {
      error = err instanceof Error ? err.message : 'Unable to load routes right now.';
    } finally {
      loading = false;
    }
  });

  $: safeRouteCount = routes.filter((route) => route.safeUrl).length;
  $: coveredCountries = new Set(routes.map((route) => route.countryLabel).filter((value) => value !== 'Country not listed')).size;
  $: coveredSources = new Set(routes.map((route) => route.sourceLabel).filter((value) => value !== 'Unavailable')).size;
  $: classifiedRoutes = routes.filter((route) => !['Missing', 'Unclassified'].includes(route.activityLabel)).length;
</script>

<svelte:head>
  <title>Akao | Route Explorer</title>
  <meta
    name="description"
    content="Explore Singapore routes with cleaner discovery, resilient filtering, and direct links back to the original sources."
  />
</svelte:head>

<main class="min-h-screen bg-sand-100 text-ink-900">
  <section class="hero-shell relative overflow-hidden px-5 pb-10 pt-8 sm:px-8 lg:px-12">
    <div class="mx-auto max-w-6xl">
      <div class="inline-flex items-center gap-2 rounded-full border border-cobalt-300/70 bg-white/70 px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-cobalt-700 shadow-sm backdrop-blur">
        Singapore route finder
      </div>

      <div class="mt-8 grid gap-10 lg:grid-cols-[1.3fr_0.8fr] lg:items-end">
        <div class="max-w-3xl">
          <p class="text-sm uppercase tracking-[0.28em] text-cobalt-700/80">Editorial route discovery</p>
          <h1 class="mt-4 max-w-3xl text-4xl font-semibold leading-tight text-ink-950 sm:text-5xl lg:text-6xl">
            Find a route that matches the ground you want to cover, not just the site it came from.
          </h1>
          <p class="mt-5 max-w-2xl text-base leading-7 text-ink-700 sm:text-lg">
            Akao now treats the scraped catalogue like a field guide: cleaner cues, resilient filters, and
            a faster path back to the original route source when the data is strong.
          </p>

          <div class="mt-8 flex flex-wrap items-center gap-4 text-sm text-ink-700">
            <a
              class="inline-flex items-center gap-2 rounded-full bg-cobalt-700 px-4 py-2 font-semibold text-white shadow-lg shadow-cobalt-700/20 transition hover:bg-cobalt-800 focus:outline-none focus:ring-2 focus:ring-cobalt-500 focus:ring-offset-2"
              href="https://github.com/gongahkia/akao"
              target="_blank"
              rel="noopener noreferrer"
              referrerpolicy="no-referrer"
            >
              View project source
            </a>
            <a
              class="inline-flex items-center gap-2 rounded-full border border-ink-300 bg-white/85 px-4 py-2 font-semibold text-ink-800 transition hover:border-cobalt-400 hover:text-cobalt-700 focus:outline-none focus:ring-2 focus:ring-cobalt-500 focus:ring-offset-2"
              href="https://gabrielongzm.com"
              target="_blank"
              rel="noopener noreferrer"
              referrerpolicy="no-referrer"
            >
              Built by Gabriel Ong
            </a>
          </div>
        </div>

        <aside class="rounded-[2rem] border border-white/70 bg-white/70 p-6 shadow-xl shadow-cobalt-900/8 backdrop-blur">
          <p class="text-xs font-semibold uppercase tracking-[0.28em] text-cobalt-700">Field note</p>
          <blockquote class="mt-4 text-2xl font-medium leading-snug text-ink-900">
            “History isn’t just in books; it’s in the trails we tread and the stories we tell.”
          </blockquote>
          <p class="mt-4 text-sm font-semibold text-ink-600">Beau Miles</p>
          <p class="mt-8 text-sm leading-6 text-ink-600">
            Routes are still sourced from the same static dataset. The refresh focuses on discovery,
            presentation, and safer outbound navigation only.
          </p>
        </aside>
      </div>

      <div class="mt-10 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <article class="stat-panel">
          <p class="stat-label">Routes indexed</p>
          <p class="stat-value">{routes.length || '...'}</p>
          <p class="stat-note">All entries come from the existing `routes.json` export.</p>
        </article>
        <article class="stat-panel">
          <p class="stat-label">Openable links</p>
          <p class="stat-value">{safeRouteCount || 0}</p>
          <p class="stat-note">Unsafe or malformed route URLs are not exposed as live links.</p>
        </article>
        <article class="stat-panel">
          <p class="stat-label">Sources surfaced</p>
          <p class="stat-value">{coveredSources || 0}</p>
          <p class="stat-note">Domains are inferred directly from the route URLs already in the dataset.</p>
        </article>
        <article class="stat-panel">
          <p class="stat-label">Activity coverage</p>
          <p class="stat-value">{classifiedRoutes || 0}</p>
          <p class="stat-note">
            Dirty activity strings are normalized into useful buckets without changing the raw data.
          </p>
        </article>
      </div>

      <div class="mt-4 text-sm text-ink-600">
        {#if coveredCountries > 0}
          Coverage spans {coveredCountries} country bucket{coveredCountries === 1 ? '' : 's'}, with Singapore dominating the current scrape.
        {/if}
      </div>
    </div>
  </section>

  <section class="px-5 pb-16 sm:px-8 lg:px-12">
    <div class="mx-auto max-w-6xl">
      {#if loading}
        <div class="rounded-[2rem] border border-sage-200 bg-white/80 p-8 shadow-lg">
          <p class="text-sm font-semibold uppercase tracking-[0.2em] text-cobalt-700">Loading routes</p>
          <p class="mt-3 max-w-2xl text-base text-ink-700">
            Pulling the latest static route catalogue into the explorer.
          </p>
        </div>
      {:else if error}
        <div class="rounded-[2rem] border border-rose-200 bg-rose-50/90 p-8 text-rose-900 shadow-lg">
          <p class="text-sm font-semibold uppercase tracking-[0.2em]">Routes unavailable</p>
          <p class="mt-3 text-base">{error}</p>
        </div>
      {:else}
        <RouteTable {routes} />
      {/if}
    </div>
  </section>
</main>
