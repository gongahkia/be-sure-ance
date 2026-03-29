<script lang="ts">
  type RouteRecord = {
    id: string;
    routeName: string;
    summary: string;
    locationLabel: string;
    countryLabel: string;
    activityLabel: string;
    terrainLabel: string;
    distanceLabel: string;
    elevationLabel: string;
    viewsLabel: string;
    sourceLabel: string;
    safeUrl: string | null;
    searchText: string;
  };

  export let routes: RouteRecord[] = [];

  let query = '';
  let activityFilter = 'all';
  let terrainFilter = 'all';
  let countryFilter = 'all';
  let sourceFilter = 'all';

  const filterOrder = ['Running', 'Walking', 'Cycling', 'Unclassified', 'Missing'];
  const terrainOrder = ['Road', 'Mixed', 'Off-Road', 'Unclassified', 'Missing'];

  function orderedOptions(values: string[], order: string[]) {
    return [...new Set(values)].sort((left, right) => {
      const leftIndex = order.indexOf(left);
      const rightIndex = order.indexOf(right);

      if (leftIndex !== -1 || rightIndex !== -1) {
        return (leftIndex === -1 ? Number.MAX_SAFE_INTEGER : leftIndex) - (rightIndex === -1 ? Number.MAX_SAFE_INTEGER : rightIndex);
      }

      return left.localeCompare(right);
    });
  }

  function matchesFilter(value: string, filter: string) {
    return filter === 'all' ? true : value === filter;
  }

  function clearFilters() {
    query = '';
    activityFilter = 'all';
    terrainFilter = 'all';
    countryFilter = 'all';
    sourceFilter = 'all';
  }

  $: activityOptions = orderedOptions(routes.map((route) => route.activityLabel), filterOrder);
  $: terrainOptions = orderedOptions(routes.map((route) => route.terrainLabel), terrainOrder);
  $: countryOptions = [...new Set(routes.map((route) => route.countryLabel))].sort((left, right) => left.localeCompare(right));
  $: sourceOptions = [...new Set(routes.map((route) => route.sourceLabel))].sort((left, right) => left.localeCompare(right));

  $: filteredRoutes = routes.filter((route) => {
    const normalizedQuery = query.trim().toLowerCase();

    return (
      (!normalizedQuery || route.searchText.includes(normalizedQuery)) &&
      matchesFilter(route.activityLabel, activityFilter) &&
      matchesFilter(route.terrainLabel, terrainFilter) &&
      matchesFilter(route.countryLabel, countryFilter) &&
      matchesFilter(route.sourceLabel, sourceFilter)
    );
  });

  $: unsafeRoutes = filteredRoutes.filter((route) => !route.safeUrl).length;
</script>

<section class="rounded-[2rem] border border-sage-200/80 bg-white/85 p-4 shadow-xl shadow-cobalt-900/8 backdrop-blur sm:p-6">
  <div class="sticky top-3 z-20 rounded-[1.5rem] border border-sage-200 bg-white/92 p-4 shadow-lg shadow-cobalt-900/5 backdrop-blur">
    <div class="grid gap-3 lg:grid-cols-[2fr_repeat(4,minmax(0,1fr))]">
      <label class="field-shell lg:col-span-1">
        <span class="field-label">Search routes</span>
        <input
          bind:value={query}
          class="field-input"
          type="search"
          placeholder="Name, place, country, activity, source"
        />
      </label>

      <label class="field-shell">
        <span class="field-label">Activity bucket</span>
        <select bind:value={activityFilter} class="field-input">
          <option value="all">All activity buckets</option>
          {#each activityOptions as option}
            <option value={option}>{option}</option>
          {/each}
        </select>
      </label>

      <label class="field-shell">
        <span class="field-label">Terrain bucket</span>
        <select bind:value={terrainFilter} class="field-input">
          <option value="all">All terrain buckets</option>
          {#each terrainOptions as option}
            <option value={option}>{option}</option>
          {/each}
        </select>
      </label>

      <label class="field-shell">
        <span class="field-label">Country</span>
        <select bind:value={countryFilter} class="field-input">
          <option value="all">All countries</option>
          {#each countryOptions as option}
            <option value={option}>{option}</option>
          {/each}
        </select>
      </label>

      <label class="field-shell">
        <span class="field-label">Source domain</span>
        <select bind:value={sourceFilter} class="field-input">
          <option value="all">All sources</option>
          {#each sourceOptions as option}
            <option value={option}>{option}</option>
          {/each}
        </select>
      </label>
    </div>

    <div class="mt-4 flex flex-col gap-3 border-t border-sage-100 pt-4 text-sm text-ink-700 md:flex-row md:items-center md:justify-between">
      <div class="flex flex-wrap items-center gap-2">
        <span class="inline-flex rounded-full bg-sand-200 px-3 py-1 font-semibold text-ink-800">
          {filteredRoutes.length} of {routes.length} routes
        </span>
        {#if unsafeRoutes > 0}
          <span class="inline-flex rounded-full bg-amber-100 px-3 py-1 font-semibold text-amber-900">
            {unsafeRoutes} hidden link{unsafeRoutes === 1 ? '' : 's'}
          </span>
        {/if}
      </div>

      <button
        class="inline-flex w-fit items-center justify-center rounded-full border border-ink-300 px-4 py-2 font-semibold text-ink-800 transition hover:border-cobalt-400 hover:text-cobalt-700 focus:outline-none focus:ring-2 focus:ring-cobalt-500 focus:ring-offset-2"
        type="button"
        on:click={clearFilters}
      >
        Reset filters
      </button>
    </div>
  </div>

  {#if filteredRoutes.length === 0}
    <div class="rounded-[1.5rem] border border-dashed border-sage-200 bg-sand-100/80 p-8 text-center text-ink-700">
      <p class="text-sm font-semibold uppercase tracking-[0.2em] text-cobalt-700">No matching routes</p>
      <p class="mx-auto mt-3 max-w-xl text-base leading-7">
        The current filters do not match anything in the static dataset. Reset the explorer or widen one of the derived buckets.
      </p>
    </div>
  {:else}
    <div class="mt-6 grid gap-4 lg:hidden">
      {#each filteredRoutes as route}
        <article class="rounded-[1.5rem] border border-sage-200 bg-sand-100/65 p-5 shadow-sm">
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.22em] text-cobalt-700">{route.sourceLabel}</p>
              <h2 class="mt-2 text-xl font-semibold text-ink-950">{route.routeName}</h2>
            </div>
            <div class="flex flex-wrap gap-2">
              <span class="route-chip">{route.activityLabel}</span>
              <span class="route-chip route-chip-muted">{route.terrainLabel}</span>
            </div>
          </div>

          <p class="mt-4 text-sm leading-6 text-ink-700">{route.summary}</p>

          <dl class="mt-5 grid grid-cols-2 gap-3 text-sm">
            <div class="meta-card">
              <dt class="meta-label">Location</dt>
              <dd class="meta-value">{route.locationLabel}</dd>
            </div>
            <div class="meta-card">
              <dt class="meta-label">Country</dt>
              <dd class="meta-value">{route.countryLabel}</dd>
            </div>
            <div class="meta-card">
              <dt class="meta-label">Distance</dt>
              <dd class="meta-value">{route.distanceLabel}</dd>
            </div>
            <div class="meta-card">
              <dt class="meta-label">Elevation</dt>
              <dd class="meta-value">{route.elevationLabel}</dd>
            </div>
          </dl>

          <div class="mt-5 flex items-center justify-between gap-3">
            <div class="text-sm text-ink-600">
              Views: <span class="font-semibold text-ink-800">{route.viewsLabel}</span>
            </div>

            {#if route.safeUrl}
              <a
                class="inline-flex items-center justify-center rounded-full bg-cobalt-700 px-4 py-2 font-semibold text-white shadow-sm transition hover:bg-cobalt-800 focus:outline-none focus:ring-2 focus:ring-cobalt-500 focus:ring-offset-2"
                href={route.safeUrl}
                target="_blank"
                rel="noopener noreferrer"
                referrerpolicy="no-referrer"
              >
                Open route
              </a>
            {:else}
              <span class="inline-flex items-center justify-center rounded-full border border-amber-200 bg-amber-50 px-4 py-2 font-semibold text-amber-900">
                Link unavailable
              </span>
            {/if}
          </div>
        </article>
      {/each}
    </div>

    <div class="mt-6 hidden overflow-hidden rounded-[1.5rem] border border-sage-200 lg:block">
      <div class="overflow-x-auto">
        <table class="min-w-full border-collapse">
          <thead class="bg-cobalt-900 text-left text-sm uppercase tracking-[0.16em] text-white/90">
            <tr>
              <th class="px-5 py-4 font-semibold">Route</th>
              <th class="px-5 py-4 font-semibold">Location</th>
              <th class="px-5 py-4 font-semibold">Activity</th>
              <th class="px-5 py-4 font-semibold">Terrain</th>
              <th class="px-5 py-4 font-semibold">Distance</th>
              <th class="px-5 py-4 font-semibold">Elevation</th>
              <th class="px-5 py-4 font-semibold">Source</th>
              <th class="px-5 py-4 font-semibold">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-sage-100 bg-white">
            {#each filteredRoutes as route}
              <tr class="align-top transition hover:bg-sand-100/90">
                <td class="px-5 py-4">
                  <div class="max-w-[22rem]">
                    <p class="font-semibold text-ink-950">{route.routeName}</p>
                    <p class="mt-2 text-sm leading-6 text-ink-600">{route.summary}</p>
                  </div>
                </td>
                <td class="px-5 py-4 text-sm text-ink-700">
                  <p class="font-semibold text-ink-800">{route.locationLabel}</p>
                  <p class="mt-1 text-ink-500">{route.countryLabel}</p>
                </td>
                <td class="px-5 py-4">
                  <span class="route-chip">{route.activityLabel}</span>
                </td>
                <td class="px-5 py-4">
                  <span class="route-chip route-chip-muted">{route.terrainLabel}</span>
                </td>
                <td class="px-5 py-4 text-sm font-semibold text-ink-800">{route.distanceLabel}</td>
                <td class="px-5 py-4 text-sm font-semibold text-ink-800">{route.elevationLabel}</td>
                <td class="px-5 py-4 text-sm text-ink-700">
                  <p class="font-semibold text-ink-800">{route.sourceLabel}</p>
                  <p class="mt-1 text-ink-500">Views: {route.viewsLabel}</p>
                </td>
                <td class="px-5 py-4">
                  {#if route.safeUrl}
                    <a
                      class="inline-flex items-center justify-center rounded-full bg-cobalt-700 px-4 py-2 font-semibold text-white shadow-sm transition hover:bg-cobalt-800 focus:outline-none focus:ring-2 focus:ring-cobalt-500 focus:ring-offset-2"
                      href={route.safeUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      referrerpolicy="no-referrer"
                    >
                      Open source
                    </a>
                  {:else}
                    <span class="inline-flex items-center justify-center rounded-full border border-amber-200 bg-amber-50 px-4 py-2 font-semibold text-amber-900">
                      Link unavailable
                    </span>
                  {/if}
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>
  {/if}
</section>
