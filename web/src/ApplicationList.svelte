<script>
  import { listApplications, LANGUAGE } from './api.js'
  import Fit from './Fit.svelte'

  const applications = listApplications()
</script>

<h1>Applications</h1>

{#await applications}
  <p aria-busy="true">Loading your applications…</p>
{:then rows}
  {#if rows.length === 0}
    <article>
      No applications yet. In the shell, run <code>apply</code> and paste a job offer.
    </article>
  {:else}
    <div class="overflow-auto">
      <table class="striped">
        <thead>
          <tr>
            <th>Company</th>
            <th>Job</th>
            <th>Language</th>
            <th>Fit</th>
            <th>Verdict</th>
            <th>Status</th>
            <th>Updated</th>
          </tr>
        </thead>
        <tbody>
          {#each rows as row (row.name)}
            <tr>
              <td><a href="#/{encodeURIComponent(row.name)}">{row.company}</a></td>
              <td>{row.job_title ?? '—'}</td>
              <td>{LANGUAGE[row.language] ?? '—'}</td>
              <td><Fit value={row.fit} /></td>
              <td>{row.verdict ?? '—'}</td>
              <td>{row.status ?? '—'}</td>
              <td><small>{row.updated.replace('T', ' ')}</small></td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
    <p><small>{rows.length} application{rows.length === 1 ? '' : 's'}, newest first.</small></p>
  {/if}
{:catch error}
  <article>
    <strong>Can't load the applications.</strong>
    <p>{error.message}. Is <code>python -m brain serve</code> running?</p>
  </article>
{/await}
