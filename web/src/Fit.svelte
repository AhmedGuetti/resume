<script>
  // The fit score, 0-100, as a number and a bar.
  let { value } = $props()
</script>

{#if value === null || value === undefined}
  —
{:else}
  <span>{value}</span>
  <progress value={value} max="100" aria-label="fit {value} out of 100"></progress>
{/if}
