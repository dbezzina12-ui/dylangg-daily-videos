/**
 * 1001 Clips uploader (Google Apps Script web app, runs as Dylan).
 * Paste into the "1001 Clips Uploader" project, then Deploy -> Manage deployments -> edit -> New version.
 * The key lives in Script Properties as Hype_upload_key; every request must carry it.
 *
 * Requests (JSON POST):
 *   {key, name, size, mimeType}      -> starts an upload into 1001 Clips and returns a one-time uploadUrl.
 *                                       A file with the same name is replaced, not duplicated.
 *   {key, action: "history"}         -> recent daily data (pool, round, leader, headline...) for caption
 *                                       and headline variety.
 *   {key, action: "remember", entry} -> stores one day's data (the daily JSON) in that history.
 *   {key, action: "file", name}      -> id, size and MD5 of that file in 1001 Clips (read-only), so caption
 *                                       metadata can be added to a video that's already uploaded.
 */

const FOLDER_ID = '1waRIY_FHC3KJnmpEKEOgoLWfiL1d6xpT';   // 1001 Clips
const HISTORY_DAYS = 45;
const HISTORY_FIELDS = ['date', 'pool', 'main', 'raffle', 'multi', 'round', 'ends', 'top', 'headline', 'stream_tonight'];

function doPost(e) {
  let req;
  try { req = JSON.parse(e.postData.contents); } catch (err) { return reply({ ok: false, error: 'bad request' }); }
  const secret = PropertiesService.getScriptProperties().getProperty('Hype_upload_key');
  if (!secret || req.key !== secret) return reply({ ok: false, error: 'bad key' });
  if (req.action === 'history') return reply({ ok: true, history: readHistory() });
  if (req.action === 'remember') return remember(req.entry);
  if (req.action === 'file') return fileInfo(String(req.name || ''));
  return startUpload(req);
}

function findInFolder(name) {
  const ids = [];
  const files = DriveApp.getFolderById(FOLDER_ID).getFilesByName(name);
  while (files.hasNext()) {
    const f = files.next();
    if (!f.isTrashed()) ids.push(f.getId());
  }
  return ids;
}

function fileInfo(name) {
  const ids = findInFolder(name);
  if (ids.length !== 1) return reply({ ok: false, error: ids.length ? 'more than one ' + name + ' in 1001 Clips' : 'no ' + name + ' in 1001 Clips' });
  const res = UrlFetchApp.fetch('https://www.googleapis.com/drive/v3/files/' + ids[0] + '?fields=id,name,size,md5Checksum&supportsAllDrives=true',
    { headers: { Authorization: 'Bearer ' + ScriptApp.getOAuthToken() }, muteHttpExceptions: true });
  if (res.getResponseCode() !== 200) return reply({ ok: false, error: 'drive said ' + res.getResponseCode() });
  return reply(Object.assign({ ok: true }, JSON.parse(res.getContentText())));
}

function startUpload(req) {
  const name = String(req.name || 'hype_edit.mp4').slice(0, 200);
  const type = String(req.mimeType || 'video/mp4');
  const existing = findInFolder(name);
  if (existing.length > 1) return reply({ ok: false, error: 'more than one ' + name + ' in 1001 Clips; nothing replaced' });

  const headers = { Authorization: 'Bearer ' + ScriptApp.getOAuthToken(), 'X-Upload-Content-Type': type };
  if (req.size) headers['X-Upload-Content-Length'] = String(Number(req.size));
  const qs = 'uploadType=resumable&supportsAllDrives=true&fields=id,name,size,md5Checksum';
  const meta = { name: name, mimeType: type };
  let url, method;
  if (existing.length) {
    url = 'https://www.googleapis.com/upload/drive/v3/files/' + existing[0] + '?' + qs; method = 'patch';
  } else {
    meta.parents = [FOLDER_ID];
    url = 'https://www.googleapis.com/upload/drive/v3/files?' + qs; method = 'post';
  }
  const res = UrlFetchApp.fetch(url, {
    method: method, contentType: 'application/json; charset=UTF-8', headers: headers,
    payload: JSON.stringify(meta), muteHttpExceptions: true });
  if (res.getResponseCode() !== 200) {
    return reply({ ok: false, error: 'drive said ' + res.getResponseCode() + ': ' + res.getContentText() });
  }
  const all = res.getAllHeaders();
  return reply({ ok: true, uploadUrl: all['Location'] || all['location'], replaced: existing.length > 0 });
}

function readHistory() {
  const props = PropertiesService.getScriptProperties().getProperties();
  return Object.keys(props).filter(k => /^day:\d{4}-\d{2}-\d{2}$/.test(k)).sort()
    .slice(-HISTORY_DAYS).map(k => JSON.parse(props[k]));
}

function remember(entry) {
  if (!entry || !/^\d{4}-\d{2}-\d{2}$/.test(String(entry.date))) return reply({ ok: false, error: 'bad entry' });
  const clean = {};
  HISTORY_FIELDS.forEach(k => { if (entry[k] !== undefined) clean[k] = entry[k]; });
  if (Array.isArray(clean.top)) clean.top = clean.top.slice(0, 5);
  const text = JSON.stringify(clean);
  if (text.length > 8000) return reply({ ok: false, error: 'entry too large' });
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const store = PropertiesService.getScriptProperties();
    store.setProperty('day:' + clean.date, text);
    const days = Object.keys(store.getProperties()).filter(k => /^day:/.test(k)).sort();
    days.slice(0, Math.max(0, days.length - HISTORY_DAYS)).forEach(k => store.deleteProperty(k));
  } finally {
    lock.releaseLock();
  }
  return reply({ ok: true });
}

function reply(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

// Run once from the editor (select "authorize" and press Run) to grant Drive access.
function authorize() {
  Logger.log('Uploads will go to: ' + DriveApp.getFolderById(FOLDER_ID).getName());
}
