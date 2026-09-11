'use client'

import { useEffect, useState } from 'react'

// A display preference only. It does not replace agent identity or server memory.
export default function ButlerWelcome() {
  const [name, setName] = useState('')
  const [draft, setDraft] = useState('')
  const [notice, setNotice] = useState('')
  const key = () => `goaa_butler_display_name_v1:${window.localStorage.getItem('client_username') || 'guest'}`
  useEffect(() => {
    const read = () => { try { const saved = window.localStorage.getItem(key()) || ''; setName(saved); setDraft(saved) } catch { setNotice('此浏览器暂时无法保存昵称。') } }
    read()
    window.addEventListener('storage', read)
    return () => window.removeEventListener('storage', read)
  }, [])
  function save() {
    const clean = draft.trim().slice(0, 24)
    if (!clean) return
    try { window.localStorage.setItem(key(), clean); setName(clean); setNotice('名字已保存在此浏览器。') }
    catch { setNotice('保存失败，请稍后再试。') }
  }
  return <div className="chat-row assistant butler-welcome">
    <span className="chat-avatar goaa" aria-hidden="true">G</span>
    <div className="chat-bubble assistant-bubble"><b>{name ? `${name} · 您的专属 AI 管家` : '您好，我是您的专属 AI 管家'}</b>
      <p>您可以直接说需求，也可以把信件、照片交给我。我们在这里整理信息、跟进事项；需要专业人士时，再由您确认对接。</p>
      <details><summary>{name ? '修改管家昵称' : '您愿意给我起个名字吗？'}</summary><div className="butler-name-editor"><label>管家昵称<input value={draft} maxLength={24} onChange={event => setDraft(event.target.value)} placeholder="例如：小安" /></label><button type="button" className="butler-secondary" disabled={!draft.trim()} onClick={save}>记住名字</button></div><small>昵称保存在此浏览器，不代表跨设备同步已开通。</small></details>
      {notice && <small role="status">{notice}</small>}
    </div>
  </div>
}
