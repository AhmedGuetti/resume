// The JSON API of `python -m brain serve` (brain/app/web.py).
async function get(url) {
  const response = await fetch(url)
  const data = await response.json()
  if (!response.ok) throw new Error(data.error ?? `${response.status} ${response.statusText}`)
  return data
}

export const listApplications = () => get('/api/applications')
export const getApplication = (name) => get(`/api/applications/${encodeURIComponent(name)}`)

export const LANGUAGE = { en: 'English', fr: 'French' }
