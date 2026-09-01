import { useEffect, useRef } from 'react'

/**
 * Поток золотых искр, летящих снизу вверх.
 * Рисует на canvas, перекрывающем экран.
 */
export default function Sparks({ on = true }) {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    let W = 0, H = 0
    const particles = []
    const COUNT = 46

    let raf = 0
    let cancelled = false

    function resize() {
      const dpr = Math.min(window.devicePixelRatio || 1, 2)
      W = window.innerWidth
      H = window.innerHeight
      canvas.width = W * dpr
      canvas.height = H * dpr
      canvas.style.width = W + 'px'
      canvas.style.height = H + 'px'
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    }

    function spawn() {
      return {
        x: Math.random() * W,
        y: H + 10,
        tx: Math.random() * W,
        ty: -20,
        t: Math.random(),
        speed: 0.0020 + Math.random() * 0.0038,
        phase: Math.random() * Math.PI * 2,
        freq: 1.5 + Math.random() * 2.6,
        amp: 6 + Math.random() * 22,
        size: 0.7 + Math.random() * 1.9,
        life: 0.5 + Math.random() * 0.5,
      }
    }

    function reset() {
      particles.length = 0
      for (let i = 0; i < COUNT; i++) {
        const p = spawn()
        p.t = Math.random()
        particles.push(p)
      }
    }

    function frame() {
        if (cancelled) return
        ctx.clearRect(0, 0, W, H)

        if (!on) {
          raf = requestAnimationFrame(frame)
          return
        }

        ctx.shadowBlur = 8
        ctx.shadowColor = 'rgba(240, 180, 41, 0.95)'

        for (let i = 0; i < particles.length; i++) {
          const p = particles[i]
          p.t += p.speed
          if (p.t >= 1) {
            particles[i] = spawn()
            continue
          }
          const e = p.t * p.t * (3 - 2 * p.t)
          const wobble = Math.sin(p.t * p.freq * Math.PI * 2 + p.phase) * p.amp * (1 - p.t)
          const x = p.x + (p.tx - p.x) * e + wobble
          const y = p.y + (p.ty - p.y) * e
          const alpha = Math.sin(p.t * Math.PI) * p.life
          ctx.globalAlpha = alpha
          ctx.fillStyle = '#ffd47a'
          ctx.beginPath()
          ctx.arc(x, y, p.size, 0, Math.PI * 2)
          ctx.fill()
        }

        ctx.globalAlpha = 1
        ctx.shadowBlur = 0
        raf = requestAnimationFrame(frame)
      }

    resize()
    reset()
    raf = requestAnimationFrame(frame)
    window.addEventListener('resize', () => { resize(); reset() })

    return () => {
      cancelled = true
      cancelAnimationFrame(raf)
      window.removeEventListener('resize', () => { resize(); reset() })
    }
  }, [on])

  return <canvas ref={canvasRef} className="holo-sparks" />
}