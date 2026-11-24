<script>
  import ApplicationList from './ApplicationList.svelte'
  import ApplicationDetail from './ApplicationDetail.svelte'

  // #/acme shows one application; anything else shows the list.
  const current = () => decodeURIComponent(location.hash.replace(/^#\/?/, ''))
  let name = $state(current())
</script>

<svelte:window onhashchange={() => (name = current())} />

<header class="container">
  <nav>
    <ul><li><a href="#/"><strong>Ninurta</strong></a></li></ul>
    <ul><li><small>Applications in cv/company/ · apply from the shell</small></li></ul>
  </nav>
</header>

<main class="container">
  {#if name}
    {#key name}<ApplicationDetail {name} />{/key}
  {:else}
    <ApplicationList />
  {/if}
</main>
