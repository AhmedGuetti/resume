<script>
  import { getApplication, LANGUAGE } from './api.js'
  import Fit from './Fit.svelte'

  let { name } = $props()
  const application = getApplication(name)

  const label = { resume: 'Resume', letter: 'Cover letter' }

  // The facts worth showing, in this order, when the offer gave them.
  const FACTS = [
    ['location', 'Location'], ['work_mode', 'Work mode'], ['contract_type', 'Contract'],
    ['seniority', 'Seniority'], ['experience_years', 'Experience'], ['education', 'Education'],
    ['start_date', 'Start'], ['recruiter', 'Recruiter'], ['source', 'Source'],
  ]
</script>

<p><a href="#/">← All applications</a></p>

{#await application}
  <p aria-busy="true">Loading…</p>
{:then app}
  {@const r = app.record ?? {}}
  <hgroup>
    <h1>{app.company}</h1>
    <p>{app.job_title ?? 'Job title not found'} · {LANGUAGE[app.language] ?? 'language unknown'}</p>
  </hgroup>

  {#if app.error}<article><strong>job.json can't be read:</strong> {app.error}</article>{/if}

  <div class="grid">
    <article>
      <header>Documents</header>
      {#if app.documents.length}
        <ul>
          {#each app.documents as doc}
            <li><a href={doc.url} target="_blank" rel="noopener">{label[doc.kind]} ({LANGUAGE[doc.lang]})</a></li>
          {/each}
        </ul>
      {:else}
        <p>No PDF yet. In the shell: <code>resume {app.name}</code> or <code>letter {app.name}</code>.</p>
      {/if}
    </article>

    <article>
      <header>Where you stand</header>
      <p>Fit: <Fit value={app.fit} /></p>
      <p>Verdict: <strong>{app.verdict ?? 'not scored yet'}</strong></p>
      {#if r.position?.reasons?.length}<p><small>{r.position.reasons.join(' · ')}</small></p>{/if}
      <p>Status: {app.status ?? '—'}</p>
    </article>
  </div>

  <article>
    <header>The offer</header>
    <table>
      <tbody>
        {#each FACTS as [key, title]}
          {#if r[key]}<tr><th scope="row">{title}</th><td>{r[key]}</td></tr>{/if}
        {/each}
        {#if r.salary}<tr><th scope="row">Salary</th><td>{r.salary.text}</td></tr>{/if}
        {#if r.posted}<tr><th scope="row">Posted</th><td>{r.posted.date ?? r.posted.text}</td></tr>{/if}
        {#if r.applicants}<tr><th scope="row">Applicants</th><td>{r.applicants.text}</td></tr>{/if}
        {#if r.url}<tr><th scope="row">Link</th><td><a href={r.url} target="_blank" rel="noopener">{r.url}</a></td></tr>{/if}
      </tbody>
    </table>

    {#if r.skills_required?.length}
      <h6>Required</h6>
      <p>{r.skills_required.join(' · ')}</p>
    {/if}
    {#if r.skills_nice_to_have?.length}
      <h6>Nice to have</h6>
      <p>{r.skills_nice_to_have.join(' · ')}</p>
    {/if}
  </article>

  {#if r.fit?.requirements?.length}
    <article>
      <header>Requirements</header>
      <div class="overflow-auto">
        <table>
          <thead><tr><th>Requirement</th><th>Kind</th><th>Status</th><th>On this resume</th></tr></thead>
          <tbody>
            {#each r.fit.requirements as req}
              <tr>
                <td>{req.text}</td>
                <td>{req.kind}</td>
                <td>{req.status}</td>
                <td>{req.on_resume ? 'yes' : 'no'}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </article>
  {/if}

  {#if app.offer}
    <details>
      <summary>Full offer text</summary>
      <pre>{app.offer}</pre>
    </details>
  {/if}
{:catch error}
  <article><strong>Can't load this application.</strong> {error.message}</article>
{/await}
