import { useEffect, useState } from 'react'

// v2: для максимальной производительности/скорости по умолчанию — простой
// визуал. Голограмму включают вручную в Настройках (тумблер «Голограмма»).
const KEY = 'ai-smolagents:holo:v2'

const DEFAULTS = {
  enabled: false,
  sparks: true,
  scan: true,
  sheen: true,
  float: true,
  tilt: 6,
  stageX: -110,
  stageY: -20,
}

function load() {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return DEFAULTS
    const parsed = JSON.parse(raw)
    return { ...DEFAULTS, ...parsed }
  } catch {
    return DEFAULTS
  }
}

function save(s) {
  try {
    localStorage.setItem(KEY, JSON.stringify(s))
  } catch {}
}

export function useHoloSettings() {
  const [s, setS] = useState(load)

  useEffect(() => { save(s) }, [s])

  // Применяем CSS-переменные на корень документа
  useEffect(() => {
    const root = document.documentElement
    root.style.setProperty('--tilt', s.tilt + 'deg')
    root.style.setProperty('--stage-x', s.stageX + 'px')
    root.style.setProperty('--stage-y', s.stageY + 'px')
  }, [s.tilt, s.stageX, s.stageY])

  const update = (patch) => setS(prev => ({ ...prev, ...patch }))
  const toggle = (key) => setS(prev => ({ ...prev, [key]: !prev[key] }))

  return { settings: s, update, toggle }
}