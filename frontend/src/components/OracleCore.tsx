import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion'
import { CSSProperties, useEffect } from 'react'

const engines = [
  { name: 'Tarot', glyph: 'Sun' },
  { name: 'Wenwang', glyph: 'Hex' },
  { name: 'BaZi', glyph: 'Five' },
  { name: 'Ziwei', glyph: 'Star' },
  { name: 'Astrology', glyph: 'Orbit' },
  { name: 'Market Pulse', glyph: 'Wave' },
]

const engineOrbits = [
  { angle: '205deg', duration: '38s', delay: '0s', radius: '29rem' },
  { angle: '175deg', duration: '42s', delay: '-8s', radius: '31rem' },
  { angle: '145deg', duration: '36s', delay: '-16s', radius: '28rem' },
  { angle: '-35deg', duration: '40s', delay: '-24s', radius: '28rem' },
  { angle: '5deg', duration: '44s', delay: '-30s', radius: '31rem' },
  { angle: '35deg', duration: '37s', delay: '-12s', radius: '29rem' },
]

export const OracleCore = ({ status = 'idle' }: { status?: 'idle' | 'generating' | 'success' }) => {
  const mouseX = useMotionValue(typeof window === 'undefined' ? 0 : window.innerWidth / 2)
  const mouseY = useMotionValue(typeof window === 'undefined' ? 0 : window.innerHeight / 2)
  const rotateX = useSpring(useTransform(mouseY, [0, typeof window === 'undefined' ? 900 : window.innerHeight], [13, -13]), { stiffness: 80, damping: 20 })
  const rotateY = useSpring(useTransform(mouseX, [0, typeof window === 'undefined' ? 1440 : window.innerWidth], [-15, 15]), { stiffness: 80, damping: 20 })

  useEffect(() => {
    const handleMouseMove = (event: MouseEvent) => {
      mouseX.set(event.clientX)
      mouseY.set(event.clientY)
    }
    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [mouseX, mouseY])

  return (
    <div className="oracle-core" aria-label="Liquid oracle core">
      <motion.div className="oracle-stage" style={{ rotateX, rotateY }}>
        <div className="oracle-pedestal" />
        <div className="oracle-ring ring-a" />
        <div className="oracle-ring ring-b" />
        <div className="oracle-ring ring-c" />

        <motion.div
          className={`oracle-orb ${status}`}
          animate={{
            scale: status === 'generating' ? [1, 1.05, 0.98, 1.03, 1] : [1, 1.015, 1],
          }}
          transition={{ duration: status === 'generating' ? 2.2 : 6, repeat: Infinity, ease: 'easeInOut' }}
        >
          <div className="oracle-meridian" />
          <div className="oracle-constellation">
            <i />
            <i />
            <i />
            <i />
          </div>
          <motion.div
            className="oracle-liquid"
            animate={{ rotate: 360, borderRadius: ['48% 52% 55% 45%', '57% 43% 44% 56%', '48% 52% 55% 45%'] }}
            transition={{ rotate: { duration: 18, repeat: Infinity, ease: 'linear' }, borderRadius: { duration: 7, repeat: Infinity, ease: 'easeInOut' } }}
          />
          <div className="oracle-compass" />
          <div className="oracle-glare" />
          <div className="oracle-lens" />
        </motion.div>

        {engines.map((engine, index) => {
          const orbit = engineOrbits[index]
          return (
            <div
              key={engine.name}
              className="engine-token visible"
              style={{
                '--angle': orbit.angle,
                '--duration': orbit.duration,
                '--delay': orbit.delay,
                '--radius': orbit.radius,
              } as CSSProperties}
            >
              <span><i>{engine.glyph}</i>{engine.name}</span>
            </div>
          )
        })}
      </motion.div>
    </div>
  )
}
