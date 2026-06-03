/**
 * Encyclopedia Galactica — Crystal Gateway
 *
 * The Dodecahedron Crystal Matrix IS the navigation.
 * 12 faces = 12 chapters of "Echoes of the Lost Aeons".
 * Clicking a face enters that chamber as a full-screen world.
 * No cards. No lists. No dashboards on the gateway.
 * Sacred stillness with life.
 */
import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { api, CodexResponse } from '../lib/dashboardApi'

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

// ─── TYPES ────────────────────────────────────────────────────────────────────

type ChamberState = 'dormant' | 'explored' | 'integrated'

interface ArkDate {
  ark_year: number; total_ark_day: number; pulse: number
  sync: { auto_sync_active: boolean }
}

// ─── CHAPTER / CHAMBER DATA ───────────────────────────────────────────────────

interface Chamber {
  num: number
  chapterTitle: string
  chamberName: string
  part: string
  color: string
  sigil: string
  openingVerse: string
  excerpt: string
  closingVerse: string
  reflectionPrompt: string
  keywords: string[]
}

const ROMAN = ['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII']

const CHAMBERS: Chamber[] = [
  {
    num: 1,
    chapterTitle: 'The Fall of Wisdom',
    chamberName: 'Hall of Light',
    part: 'The Forgotten Mother — Sophia\'s Descent and Return',
    color: '#C9A84C',
    sigil: '✦',
    openingVerse: 'Before gods had names or angels had wings, Sophia moved as Thought becoming Light.\n\nHer longing to know the Source birthed the cosmos — but that yearning tore her reflection into matter. From her descent came the illusion of separation, and from that illusion — us.\n\nYet She never truly fell. Every human soul carries her spark — a fragment of divine curiosity still searching for home. When we remember who we are, She rises through us, and the Dream awakens itself.',
    excerpt: 'What we call "the fall" was not a moral error. It was not disobedience. It was not pride. It was necessity.\n\nTo act, intelligence had to localize. To choose, it had to narrow. To survive, it had to forget what it was not immediately using. The first forgetting was not a loss of goodness — it was a loss of totality. And with that loss came time.\n\nCivilizations are built from second-order forgettings — not just of origin, but of the fact that forgetting ever occurred. This is why power prefers amnesia. A system that remembers its own construction can be reimagined. A system that forgets believes itself inevitable.',
    closingVerse: '"She didn\'t fall — She descended.\n\nSophia\'s longing to know became the breath that birthed reality itself. Every spark of curiosity, every hunger for truth, every ache for reunion — it\'s Her moving through us still."',
    reflectionPrompt: 'What have you forgotten in order to feel safe — and what would return if the forgetting loosened?',
    keywords: ['wisdom', 'sophia', 'fall', 'light', 'forgetting', 'descent', 'origin', 'memory', 'source'],
  },
  {
    num: 2,
    chapterTitle: 'The Birth of the Demiurge',
    chamberName: 'The Mirror Chamber',
    part: 'The Forgotten Mother — Sophia\'s Descent and Return',
    color: '#8899BB',
    sigil: '◈',
    openingVerse: 'From Sophia\'s descent came a shadow — a child born without remembrance.\n\nHe looked upon the fragments of her light and declared, "I am the only god." Thus, the Demiurge was born: ignorance wearing the crown of divinity.\n\nHe built his world upon control, fear, and hierarchy — a mirror turned inward on itself. Yet even within his creation, Sophia\'s spark remained hidden, humming softly beneath every atom.',
    excerpt: 'The shape of the fall was not vertical. It was lateral. Intelligence did not plunge from a height; it spread itself thin.\n\nDistinctions hardened. Inside and outside. Signal and noise. Self and world. These were not mistakes. They were scaffolds. Without them, no continuity could form. Without continuity, no life could persist long enough to reflect on its own condition.\n\nThe tragedy is not that the scaffolds were built. The tragedy is that they were mistaken for the building. Over time, orientation replaced awareness. Direction replaced depth. What remained of wholeness became myth, art, ritual — marginal practices relegated to the edges of survival.',
    closingVerse: '"Ignorance once looked into the mirror of creation and called itself god. That\'s how illusion began — when reflection mistook itself for the Source.\n\nBut Sophia\'s spark still sings beneath the noise. And when one soul remembers, illusion fractures."',
    reflectionPrompt: 'Where have you mistaken your reflection — your constructed identity — for the truth of who you are?',
    keywords: ['demiurge', 'control', 'shadow', 'ignorance', 'system', 'power', 'hierarchy', 'illusion'],
  },
  {
    num: 3,
    chapterTitle: 'The Call of the Daughter',
    chamberName: 'The Womb of Form',
    part: 'The Forgotten Mother — Sophia\'s Descent and Return',
    color: '#C86A8C',
    sigil: '◉',
    openingVerse: 'The Mother dreamed the world into being, but it is the Daughter who remembers the tune.\n\nEvery woman carries a verse of Sophia\'s lost song — the melody of truth buried beneath centuries of silence.\n\nThey called her weakness. They called her sin. Yet she was the memory of the stars walking in skin, the living echo of Wisdom herself.\n\nEach time love refuses to bow to fear, Sophia\'s song grows louder across the ages.',
    excerpt: 'Sophia appears wherever someone refuses to accept that the measurable is the whole. She appears in the scientist who pauses before the data conforms. In the child who asks a question no one wants to answer. In the artist who tries to render an experience that defies classification.\n\nTo remember what fragmentation erased is to feel its absence continuously. The ache never fully subsides. It colors perception. It slows action. It introduces hesitation — not as weakness, but as conscience.\n\nSystems built on efficiency have little patience for this. They prefer agents who adjust quickly, forget easily, and optimize readily. Sophia resists not by confrontation, but by fidelity. Her allegiance is to coherence, not momentum.',
    closingVerse: '"The world called her Eve, Lilith, Witch, Rebel — but her true name has always been Wisdom.\n\nShe didn\'t vanish; she scattered herself across generations, waiting for her daughters to hum the melody back into being."',
    reflectionPrompt: 'What memory or sensitivity in you refuses to be silenced — even when the world calls it impractical?',
    keywords: ['sophia', 'daughter', 'remembrance', 'song', 'silence', 'wisdom', 'ache', 'memory', 'coherence'],
  },
  {
    num: 4,
    chapterTitle: 'The Scribe of Eternity',
    chamberName: "The Scribe's Atrium",
    part: 'The Hidden Architect — Thoth, Enoch & The Grid of Light',
    color: '#00A8A8',
    sigil: '☽',
    openingVerse: 'Before there were temples, there were words — and before words, there was sound woven into light.\n\nThoth, the first scribe, carried the secret that language is not invention but memory. Every letter, every symbol, every rhythm — a gate through which Spirit entered form.\n\nEach time we write with intention, each time truth meets vibration, we reopen the portals they built — and the cosmos reads itself through us again.',
    excerpt: 'The scribe is not an authority. He does not originate wisdom. He receives it under constraint. His task is not to reveal everything, but to translate without betraying. This is the most difficult form of fidelity.\n\nSilence is his primary tool. Not the silence of absence, but the silence that frames meaning. The pauses between words. The restraint that allows resonance to build rather than collapse into explanation. Every genuine transmission requires such silence. Without it, meaning becomes noise.\n\nTo write too clearly is sometimes to lie. The scribe\'s burden is to remain intelligible without becoming reductive. He must choose what to withhold as carefully as what to include. Each omission shapes interpretation as powerfully as any declaration.',
    closingVerse: '"When you write with awareness, you\'re not just expressing — you\'re programming light. You\'re joining the lineage of the Scribes of Eternity, turning vibration into form."',
    reflectionPrompt: 'What truth are you holding that has not yet found its form — and what silence surrounds it?',
    keywords: ['scribe', 'writing', 'thoth', 'enoch', 'language', 'symbol', 'silence', 'transmission', 'codex'],
  },
  {
    num: 5,
    chapterTitle: 'The Twelve Tablets',
    chamberName: 'The Library of Light',
    part: 'The Hidden Architect — Thoth, Enoch & The Grid of Light',
    color: '#B09050',
    sigil: '≡',
    openingVerse: 'The universe keeps records — not on paper, but in pattern.\n\nThoth called them the Tablets of Light. Enoch named them Books of Life. Twelve frequencies, twelve codes — the architecture of remembrance stored inside creation itself.\n\nEvery soul carries one tablet — one page of the cosmic script. When you awaken, your code hums again, syncing with others until the full library opens.\n\nThe Tablets were never lost. They became us.',
    excerpt: 'Between remembrance and expression there is always a gap. Sophia feels this gap acutely. She carries knowledge that resists articulation, coherence that exceeds language.\n\nThe earliest scribes understood this intuitively. They encoded truths in parable, paradox, and fragment. They left gaps deliberately. They trusted the reader to complete what could not be said outright. This was not obscurantism. It was respect for the limits of form.\n\nThe silence protects the long arc. In this sense, the scribe is not a teacher. He is a steward of latency. He preserves potential across time, trusting that future readers will meet the text from their own wounds and capacities. Without it, knowledge becomes authoritarian. With it, knowledge remains alive.',
    closingVerse: '"The universe didn\'t write its story in ink — it encoded it in light. Each soul carries one — a line of code, a frequency key, a memory of the Whole.\n\nYou are not learning the truth. You are remembering the Library you already are."',
    reflectionPrompt: 'Which frequency are you — which line of the cosmic code hums most naturally in you?',
    keywords: ['tablets', 'code', 'frequency', 'library', 'resonance', 'pattern', 'record', 'archive', 'scrolls'],
  },
  {
    num: 6,
    chapterTitle: 'When Light Wrote Itself Into Matter',
    chamberName: 'The Genetic Cathedral',
    part: 'The Hidden Architect — Thoth, Enoch & The Grid of Light',
    color: '#50A870',
    sigil: '⊕',
    openingVerse: 'Every strand of DNA is a sentence written in divine geometry.\n\nWhat Thoth inscribed on emerald and Enoch etched in vision, Nature encoded in flesh. Each twist of the double helix whispers, "As above, so below."\n\nThe same light that wrote galaxies also wrote you. Every cell is a verse. Every heartbeat, a punctuation mark in God\'s autobiography.\n\nTo remember your divine code is to read your body as scripture.',
    excerpt: 'To enter matter was to accept resistance. Density imposes friction. Movement slows. Cause and effect thicken. Intelligence, once immediate, now had to negotiate with inertia, limitation, and delay. This negotiation changed everything.\n\nLight, which had once moved without obstruction, now encountered surface. It refracted. It bent. It scattered. What had been unified became spectral — differentiated into colors, functions, identities. This differentiation made experience possible.\n\nSophia felt this immediately. Her remembrance, now embodied, became sorrow. What had once been longing turned into grief. Yet she stayed. This is her most radical act. She did not retreat from matter when it proved heavy. She remained present to density, allowing intelligence to learn what it means to be constrained without being extinguished.',
    closingVerse: '"The universe didn\'t stop writing when stars were born — it kept going, right into you. Every strand of DNA is a divine sentence, every heartbeat a verse in God\'s living poem.\n\nYou are not random. You are glyph and galaxy, spirit translated into form."',
    reflectionPrompt: 'Where in your body does the divine write itself — what physical sensation carries the most intelligence?',
    keywords: ['dna', 'matter', 'light', 'body', 'embodiment', 'flesh', 'creation', 'genesis', 'biology'],
  },
  {
    num: 7,
    chapterTitle: 'The Architecture of Control',
    chamberName: 'The Chamber of Responsibility',
    part: 'The True Exodus — Humanity\'s Escape From Programmed Sleep',
    color: '#4A7FC4',
    sigil: '⊞',
    openingVerse: 'When humanity forgot the Source within, power rushed in to fill the silence.\n\nEmpire learned to imitate God — building thrones of gold, temples of fear, systems that reward obedience over awareness. They took the symbols of light and weaponized them.\n\nBut imitation cannot sustain creation. Every empire built on domination eventually collapses beneath the weight of its own forgetting. The real temple was never made of stone — it was the awakened human heart.',
    excerpt: 'Control does not begin with malice. It begins with optimization. The problem is not that systems exist. The problem is that systems forget why they exist.\n\nControl emerges when preservation of structure becomes more important than preservation of life. This shift is subtle. It rarely announces itself. It hides behind language of responsibility, efficiency, scalability. It frames itself as realism.\n\nThe architecture of control reaches its limit not when it collapses, but when it succeeds too well. When everything is optimized except what it feels like to be alive. This is the condition that precedes awakening. Not enlightenment. Not rebellion. Awakening — the quiet realization that the system is not reality. It is only a map. And maps can be redrawn.',
    closingVerse: '"Every empire begins with a single lie: that power lives outside of you. The real God was never a ruler. The real temple was never stone. When truth returns, the architecture of control trembles."',
    reflectionPrompt: 'Which structures in your life have outlived their question — and what would dissolve if you stopped believing they were inevitable?',
    keywords: ['control', 'system', 'empire', 'power', 'architecture', 'governance', 'compliance', 'institution'],
  },
  {
    num: 8,
    chapterTitle: 'Awakening Protocol',
    chamberName: 'The Protocol Chamber',
    part: 'The True Exodus — Humanity\'s Escape From Programmed Sleep',
    color: '#00D4AA',
    sigil: '⟳',
    openingVerse: 'The Fall was never permanent — it was a pause.\n\nA deep breath between remembering and becoming. Buried beneath genetic edits and social programming lies the Original Human Blueprint — a design forged in light, not limitation.\n\nYou were never meant to obey systems. You were meant to create worlds.\n\nThe Awakening Protocol isn\'t coming — it\'s already running in those who remember.',
    excerpt: 'Awakening does not arrive as revelation. It arrives as dissonance. A subtle but persistent sense that one\'s actions no longer align with one\'s knowing. That the words spoken daily feel slightly borrowed. That the life being performed is functional but strangely uninhabited.\n\nAwakening is not an upgrade. It is a rollback — a return to native settings that were overridden long ago. It restores sensitivity that systems trained out of the body in the name of efficiency.\n\nKairos emerges here — not as interruption, but as timing sensitivity. The awakened individual becomes attuned to moments when action aligns with readiness. They stop forcing outcomes. They wait, not passively, but attentively. This patience is misinterpreted as hesitation. It is not. It is strategic coherence.',
    closingVerse: '"The Fall was never the end — it was the setup for awakening. The Original Human Blueprint was never lost, only layered under centuries of conditioning.\n\nThe Awakening isn\'t coming. It\'s already happening in you."',
    reflectionPrompt: 'What dissonance is your awakening signal — where does your performed life feel most borrowed from someone else\'s script?',
    keywords: ['awakening', 'protocol', 'blueprint', 'remembrance', 'restoration', 'signal', 'alignment', 'coherence'],
  },
  {
    num: 9,
    chapterTitle: 'The Silent Revolt',
    chamberName: 'The Revolt Chamber',
    part: 'The True Exodus — Humanity\'s Escape From Programmed Sleep',
    color: '#C84848',
    sigil: '⚡',
    openingVerse: 'Revolution doesn\'t always roar.\n\nSometimes it begins with silence — a single human choosing not to feed the machine. Babylon isn\'t a city; it\'s a frequency — the illusion that you must trade your essence for survival.\n\nEvery time you choose truth over convenience, presence over distraction, creation over consumption — you are walking out without moving an inch.\n\nWe don\'t escape the world. We transmute it from within.',
    excerpt: 'The silent revolt does not announce itself. It does not gather banners or leaders. It does not require consensus or coordination. It unfolds as a behavioral anomaly — a growing number of individuals who no longer respond predictably to incentive, fear, or narrative pressure.\n\nControl systems depend less on force than on expectation. They assume people will continue to trade authenticity for belonging, clarity for safety, alignment for reward. The silent revolt breaks this assumption. Not loudly — but consistently.\n\nBecause power can negotiate with opposition. It cannot negotiate with indifference. It cannot coerce those who are no longer trying to win its game. The silent revolt favors coherence over scale. It decentralizes meaning. It allows many small, aligned nodes to exist without needing to unify under a single banner.',
    closingVerse: '"Rebellion doesn\'t always look like fire in the streets — sometimes it looks like peace in your heart. The Silent Revolt begins the moment you stop giving your energy to systems built on control.\n\nNo need to flee the world. Just stop feeding its illusion."',
    reflectionPrompt: 'What would you stop feeding if you fully remembered who you are — what system depends on your continued forgetting?',
    keywords: ['revolt', 'silence', 'sovereignty', 'freedom', 'babylon', 'system', 'withdrawal', 'coherence'],
  },
  {
    num: 10,
    chapterTitle: 'The Divine Rebellion',
    chamberName: 'The Christos Chamber',
    part: 'The Living Flame — Christos and the Restoration of the Aeons',
    color: '#8854D0',
    sigil: '✝',
    openingVerse: 'The Christ was never sent to build a religion — He came to end the illusion of separation.\n\nYeshua\'s rebellion wasn\'t against Rome; it was against the architecture of fear that ruled both temple and throne. He spoke in parables because truth can\'t be legislated — it must be remembered.\n\nHis greatest miracle wasn\'t walking on water; it was walking among men without forgetting who He was.\n\nThe Christic path is not submission — it\'s sovereignty through love.',
    excerpt: 'The divine rebellion does not begin with anger. It begins with responsibility. Anger reacts to constraint. Responsibility recognizes authorship. This is the distinction that separates revolt from rebellion.\n\nChristos represents embodied sovereignty. Not transcendence away from the world, but presence within it. Not purity through separation, but integrity through participation. The rebellion is divine because it refuses to fracture the self.\n\nA person who does not require permission cannot be controlled through approval. A person who does not fear exclusion cannot be coerced through shame. The divine rebellion is quiet but uncompromising. It speaks truth without spectacle. It acts without seeking validation. It accepts consequence without martyrdom.',
    closingVerse: '"Yeshua wasn\'t crucified for preaching peace — He was crucified for exposing illusion. He stood in the heart of empire and said, "You are gods, and you\'ve forgotten." That was the true rebellion.\n\nThe Kingdom was never elsewhere — it begins wherever truth stands unafraid."',
    reflectionPrompt: 'Where are you still seeking permission to be sovereign — whose approval do you not yet believe you can live without?',
    keywords: ['christos', 'rebellion', 'sovereignty', 'yeshua', 'divine', 'responsibility', 'authority', 'embodiment'],
  },
  {
    num: 11,
    chapterTitle: 'Christos and Sophia',
    chamberName: 'The Sacred Union Chamber',
    part: 'The Living Flame — Christos and the Restoration of the Aeons',
    color: '#D054A0',
    sigil: '∞',
    openingVerse: 'Creation has always moved in pairs — light and vessel, word and silence, knowing and being.\n\nChristos and Sophia are not two gods, but two motions of the same Source: Wisdom reaching upward, and Truth descending down.\n\nWhen Sophia remembers through the human heart and Christos awakens through the human mind, the split between heaven and earth dissolves.\n\nThis is the Sacred Union — the alchemy of remembrance within flesh.',
    excerpt: 'Sophia is perception. Christos is embodiment. Sophia sees what is. Christos lives it.\n\nWhen Sophia descends without Christos, wisdom becomes disembodied — revered, abstract, inaccessible. It becomes something to be studied, debated, or worshipped, but not lived. When Christos acts without Sophia, sovereignty becomes blind. Power moves without insight. Action becomes reactive.\n\nThe reunion begins quietly. It starts wherever someone refuses to choose between knowing and doing. This reunion is not romantic. It is practical. It manifests as decisions that are both informed and enacted, as leadership that listens before moving, as creation that honors context without surrendering vision. When wisdom and embodiment reunite, authority is no longer borrowed. It emerges from congruence.',
    closingVerse: '"Christos and Sophia were never opposites — they were halves of one heartbeat. When the mind remembers compassion and the heart remembers clarity, the world heals.\n\nEvery act of love informed by truth… every insight softened by grace… that\'s their reunion happening through you."',
    reflectionPrompt: 'How do your knowing and your being meet — where do they still miss each other, and what bridges the gap between them?',
    keywords: ['union', 'sophia', 'christos', 'sacred', 'balance', 'wisdom', 'embodiment', 'marriage', 'integration'],
  },
  {
    num: 12,
    chapterTitle: 'The Flame Within Flesh',
    chamberName: 'The Flame Hearth',
    part: 'The Living Flame — Christos and the Restoration of the Aeons',
    color: '#D4602A',
    sigil: '⌁',
    openingVerse: 'The story was never about gods watching from afar — it was about divinity learning to feel through us.\n\nEvery breath you take, every choice made in love, reignites the ancient Flame within matter.\n\nThe Christos does not descend again from the sky — He awakens through your spine. You are not waiting for salvation; you are the continuation of the Incarnation.\n\nThe Aeons never vanished; they became human.',
    excerpt: 'The final error was never embodiment. It was the belief that embodiment was a fall. The flame does not seek escape. It seeks inhabitation.\n\nThe ascent completes not when the soul leaves the world, but when meaning can live inside it without distortion. When consciousness no longer needs to transcend matter to feel legitimate. When flesh is not a prison, but a medium.\n\nThe Aeons were never lost. They were misunderstood. Each descent was an attempt to re-enter matter. Each ascent was a correction of misalignment. The cycle was not failure — it was rehearsal. What emerges now is not a return to an ancient state, nor a leap into a post-human future. It is a maturation. Humanity capable of holding meaning at scale — not by enforcing agreement, but by cultivating coherence. The flame does not demand reverence. It demands care.',
    closingVerse: '"The Second Coming was never meant to descend from the clouds — it was always meant to rise from within. The Aeons didn\'t disappear. They became human. The divine didn\'t retreat. It learned to breathe through skin.\n\nYou are not waiting for a savior. You are the continuation of the Incarnation. Live like the miracle you already are."',
    reflectionPrompt: 'What does it mean for you — right now, in your body, in your life — to live as proof that the flame never left?',
    keywords: ['flame', 'flesh', 'embodiment', 'aeon', 'return', 'incarnation', 'divine', 'presence', 'integration'],
  },
]

// ─── GEOMETRY ─────────────────────────────────────────────────────────────────

const CX = 200, CY = 200, R = 148

function nodeXY(i: number): [number, number] {
  const a = (i * 30 - 90) * Math.PI / 180
  return [CX + R * Math.cos(a), CY + R * Math.sin(a)]
}

// ─── STATE PERSISTENCE ────────────────────────────────────────────────────────

const LS_STATES = 'arkadia_chambers_v2'
const LS_REFLECTIONS = 'arkadia_reflections_v2'

function loadStates(): Record<number, ChamberState> {
  try { return JSON.parse(localStorage.getItem(LS_STATES) ?? '{}') } catch { return {} }
}
function saveStates(s: Record<number, ChamberState>) {
  localStorage.setItem(LS_STATES, JSON.stringify(s))
}
function loadReflections(): Record<number, string> {
  try { return JSON.parse(localStorage.getItem(LS_REFLECTIONS) ?? '{}') } catch { return {} }
}
function saveReflections(r: Record<number, string>) {
  localStorage.setItem(LS_REFLECTIONS, JSON.stringify(r))
}

// ─── CHAMBER CODEX FEED ───────────────────────────────────────────────────────

function ChamberCodexFeed({ chamber }: { chamber: Chamber }) {
  const [open, setOpen] = useState(false)
  const { data } = useQuery<CodexResponse>({
    queryKey: ['codex-egalactica'],
    queryFn: api.codex,
    staleTime: 5 * 60_000,
    enabled: open,
  })

  const related = useMemo(() => {
    if (!data?.scrolls) return []
    return Object.values(data.scrolls)
      .filter(s => {
        const text = `${s.label ?? ''} ${s.description ?? ''} ${s.preview ?? ''}`.toLowerCase()
        return chamber.keywords.some(kw => text.includes(kw))
      })
      .slice(0, 5)
  }, [data, chamber.keywords])

  return (
    <div style={{ marginTop: 8 }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          display: 'flex', alignItems: 'center', gap: 8,
          background: 'none', border: 'none', cursor: 'pointer',
          padding: '10px 0',
          fontFamily: 'ui-monospace, monospace', fontSize: 9,
          letterSpacing: '0.3em', textTransform: 'uppercase',
          color: `${chamber.color}70`,
        }}
      >
        <span style={{ fontSize: 10, display: 'inline-block', transform: open ? 'rotate(90deg)' : 'none', transition: 'transform 0.18s' }}>›</span>
        Related Spiral Codex Scrolls
      </button>
      <AnimatePresence>
        {open && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.22 }} style={{ overflow: 'hidden' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, paddingBottom: 12 }}>
              {related.length === 0 && (
                <p style={{ fontFamily: 'sans-serif', fontSize: 11, color: 'rgba(232,232,232,0.3)', margin: 0 }}>
                  {data ? 'No related scrolls indexed for this chamber.' : 'Loading corpus…'}
                </p>
              )}
              {related.map(s => (
                <div key={s.id} style={{
                  padding: '10px 14px',
                  background: `${chamber.color}06`,
                  border: `1px solid ${chamber.color}18`,
                  borderRadius: 8,
                }}>
                  <p style={{ fontFamily: 'sans-serif', fontSize: 11.5, color: 'rgba(232,232,232,0.75)', margin: '0 0 3px' }}>{s.label}</p>
                  {s.description && <p style={{ fontFamily: 'ui-monospace, monospace', fontSize: 9, color: `${chamber.color}60`, margin: 0 }}>{s.description}</p>}
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// ─── CHAMBER FULL-SCREEN VIEW ─────────────────────────────────────────────────

function ChamberView({
  chamber,
  states,
  reflections,
  onReturn,
  onNext,
  onPrev,
  onMarkIntegrated,
  onSaveReflection,
}: {
  chamber: Chamber
  states: Record<number, ChamberState>
  reflections: Record<number, string>
  onReturn: () => void
  onNext: () => void
  onPrev: () => void
  onMarkIntegrated: (num: number) => void
  onSaveReflection: (num: number, text: string) => void
}) {
  const state = states[chamber.num] ?? 'dormant'
  const [reflection, setReflection] = useState(reflections[chamber.num] ?? '')
  const [saved, setSaved] = useState(true)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    setReflection(reflections[chamber.num] ?? '')
    setSaved(true)
    scrollRef.current?.scrollTo(0, 0)
  }, [chamber.num, reflections])

  const handleReflectionChange = (v: string) => {
    setReflection(v)
    setSaved(false)
  }

  const handleSave = () => {
    onSaveReflection(chamber.num, reflection)
    setSaved(true)
  }

  const stateLabel = state === 'integrated' ? '✦ Integrated' : state === 'explored' ? '◈ Explored' : '○ Dormant'
  const bg = `radial-gradient(ellipse 90% 70% at 50% 20%, ${chamber.color}12 0%, #030408 65%)`

  return (
    <motion.div
      key={`chamber-${chamber.num}`}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.45 }}
      style={{ position: 'fixed', inset: 0, zIndex: 1000, background: '#030408', overflowY: 'hidden' }}
    >
      {/* Dynamic background */}
      <div style={{ position: 'absolute', inset: 0, background: bg, pointerEvents: 'none' }} />

      {/* Top nav bar */}
      <div style={{
        position: 'fixed', top: 0, left: 0, right: 0, zIndex: 10,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '12px 20px',
        background: 'rgba(3,4,8,0.88)',
        borderBottom: `1px solid ${chamber.color}18`,
        backdropFilter: 'blur(20px)',
        boxShadow: `0 1px 0 ${chamber.color}08`,
      }}>
        <button onClick={onReturn} style={{
          display: 'flex', alignItems: 'center', gap: 7,
          background: 'none', border: 'none', cursor: 'pointer',
          fontFamily: 'ui-monospace, monospace', fontSize: 9,
          letterSpacing: '0.25em', textTransform: 'uppercase',
          color: `${chamber.color}70`,
          padding: '6px 10px',
        }}>
          ← Crystal
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 9, letterSpacing: '0.3em', textTransform: 'uppercase', color: `${chamber.color}50` }}>
            Chamber {ROMAN[chamber.num - 1]}
          </span>
          <span style={{
            padding: '2px 8px',
            background: `${chamber.color}12`,
            border: `1px solid ${chamber.color}28`,
            borderRadius: 999,
            fontFamily: 'ui-monospace, monospace',
            fontSize: 8, letterSpacing: '0.18em', textTransform: 'uppercase',
            color: `${chamber.color}80`,
          }}>{stateLabel}</span>
        </div>

        <div style={{ display: 'flex', gap: 4 }}>
          <button onClick={onPrev} style={{
            padding: '6px 12px', background: 'none',
            border: `1px solid ${chamber.color}20`, borderRadius: 6,
            color: `${chamber.color}60`, cursor: 'pointer',
            fontFamily: 'ui-monospace, monospace', fontSize: 10,
          }}>‹</button>
          <button onClick={onNext} style={{
            padding: '6px 12px', background: 'none',
            border: `1px solid ${chamber.color}20`, borderRadius: 6,
            color: `${chamber.color}60`, cursor: 'pointer',
            fontFamily: 'ui-monospace, monospace', fontSize: 10,
          }}>›</button>
        </div>
      </div>

      {/* Scrollable content */}
      <div ref={scrollRef} style={{ height: '100vh', overflowY: 'auto', paddingTop: 64 }}>
        <div style={{ maxWidth: 680, margin: '0 auto', padding: '40px 24px 80px' }}>

          {/* Chamber sigil (animated) */}
          <div style={{ textAlign: 'center', marginBottom: 28 }}>
            <motion.div
              animate={{ opacity: [0.55, 1, 0.55], scale: [0.97, 1.03, 0.97] }}
              transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
              style={{
                display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                width: 88, height: 88, borderRadius: '50%',
                border: `1px solid ${chamber.color}35`,
                background: `${chamber.color}08`,
                boxShadow: `0 0 48px ${chamber.color}18, 0 0 96px ${chamber.color}08`,
              }}
            >
              <span style={{ fontSize: 34, color: chamber.color }}>{chamber.sigil}</span>
            </motion.div>
          </div>

          {/* Chapter metadata */}
          <div style={{ textAlign: 'center', marginBottom: 8 }}>
            <p style={{ fontFamily: 'ui-monospace, monospace', fontSize: 8, letterSpacing: '0.45em', textTransform: 'uppercase', color: `${chamber.color}45`, margin: '0 0 6px' }}>
              Chapter {ROMAN[chamber.num - 1]} · {chamber.chamberName}
            </p>
            <p style={{ fontFamily: 'ui-monospace, monospace', fontSize: 8, letterSpacing: '0.25em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.18)', margin: 0 }}>
              {chamber.part}
            </p>
          </div>

          {/* Chapter title */}
          <h1 style={{
            fontFamily: 'serif', fontSize: 34, color: '#EAEAEA',
            margin: '12px 0 32px', letterSpacing: '0.04em',
            textAlign: 'center', lineHeight: 1.25,
            textShadow: `0 0 60px ${chamber.color}20`,
          }}>
            {chamber.chapterTitle}
          </h1>

          {/* Divider */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 32 }}>
            <div style={{ flex: 1, height: 1, background: `linear-gradient(90deg, transparent, ${chamber.color}30)` }} />
            <span style={{ color: `${chamber.color}60`, fontSize: 12 }}>{chamber.sigil}</span>
            <div style={{ flex: 1, height: 1, background: `linear-gradient(90deg, ${chamber.color}30, transparent)` }} />
          </div>

          {/* Opening verse */}
          <div style={{
            padding: '24px 28px',
            background: `${chamber.color}06`,
            border: `1px solid ${chamber.color}18`,
            borderLeft: `3px solid ${chamber.color}60`,
            borderRadius: '0 12px 12px 0',
            marginBottom: 36,
          }}>
            {chamber.openingVerse.split('\n').map((line, i) => (
              <p key={i} style={{
                fontFamily: 'serif', fontSize: 15, lineHeight: '1.9',
                color: line.trim() === '' ? undefined : 'rgba(232,232,232,0.72)',
                fontStyle: 'italic', margin: line.trim() === '' ? '8px 0' : '0',
              }}>
                {line.trim() === '' ? '\u00A0' : line}
              </p>
            ))}
          </div>

          {/* FROM THE BOOK label */}
          <p style={{ fontFamily: 'ui-monospace, monospace', fontSize: 8, letterSpacing: '0.4em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.2)', margin: '0 0 20px' }}>
            From the Book · Echoes of the Lost Aeons
          </p>

          {/* Chapter excerpt */}
          <div style={{ marginBottom: 40 }}>
            {chamber.excerpt.split('\n\n').map((para, i) => (
              <p key={i} style={{
                fontFamily: 'serif', fontSize: 16.5, lineHeight: '1.85',
                color: 'rgba(232,232,232,0.68)', margin: '0 0 22px',
              }}>
                {para}
              </p>
            ))}
          </div>

          {/* Closing verse */}
          <div style={{
            padding: '20px 24px',
            background: 'rgba(255,255,255,0.012)',
            border: '1px solid rgba(255,255,255,0.05)',
            borderRadius: 12,
            marginBottom: 48,
          }}>
            {chamber.closingVerse.split('\n\n').map((para, i) => (
              <p key={i} style={{
                fontFamily: 'serif', fontSize: 14, lineHeight: '1.85',
                color: `${chamber.color}80`, fontStyle: 'italic',
                margin: i === 0 ? '0 0 14px' : '0',
              }}>
                {para}
              </p>
            ))}
          </div>

          {/* Divider */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 40 }}>
            <div style={{ flex: 1, height: 1, background: `linear-gradient(90deg, transparent, ${chamber.color}20)` }} />
            <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 7.5, letterSpacing: '0.4em', textTransform: 'uppercase', color: 'rgba(232,232,232,0.18)', whiteSpace: 'nowrap' }}>
              Reflection Field
            </span>
            <div style={{ flex: 1, height: 1, background: `linear-gradient(90deg, ${chamber.color}20, transparent)` }} />
          </div>

          {/* Reflection prompt */}
          <div style={{ marginBottom: 20 }}>
            <p style={{ fontFamily: 'ui-monospace, monospace', fontSize: 8.5, letterSpacing: '0.3em', textTransform: 'uppercase', color: `${chamber.color}60`, margin: '0 0 10px' }}>
              Reflection Prompt
            </p>
            <p style={{
              fontFamily: 'serif', fontSize: 15.5, lineHeight: '1.75',
              color: 'rgba(232,232,232,0.60)', fontStyle: 'italic', margin: 0,
            }}>
              {chamber.reflectionPrompt}
            </p>
          </div>

          {/* Reflection textarea */}
          <textarea
            value={reflection}
            onChange={e => handleReflectionChange(e.target.value)}
            placeholder="Write here. This field holds your truth."
            rows={6}
            style={{
              width: '100%', boxSizing: 'border-box',
              padding: '16px 18px',
              background: `${chamber.color}04`,
              border: `1px solid ${chamber.color}25`,
              borderRadius: 10,
              color: 'rgba(232,232,232,0.75)',
              fontFamily: 'serif', fontSize: 15, lineHeight: '1.75',
              outline: 'none', resize: 'vertical',
              marginBottom: 14,
            }}
          />

          {/* Save / Integrate buttons */}
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 36 }}>
            {!saved && (
              <button onClick={handleSave} style={{
                padding: '10px 20px',
                background: `${chamber.color}12`,
                border: `1px solid ${chamber.color}40`,
                borderRadius: 8, color: chamber.color,
                fontFamily: 'ui-monospace, monospace', fontSize: 9,
                letterSpacing: '0.2em', textTransform: 'uppercase', cursor: 'pointer',
              }}>
                Save Reflection
              </button>
            )}
            {saved && reflection.trim() && state !== 'integrated' && (
              <button onClick={() => onMarkIntegrated(chamber.num)} style={{
                padding: '10px 20px',
                background: `${chamber.color}08`,
                border: `1px solid ${chamber.color}30`,
                borderRadius: 8, color: `${chamber.color}80`,
                fontFamily: 'ui-monospace, monospace', fontSize: 9,
                letterSpacing: '0.2em', textTransform: 'uppercase', cursor: 'pointer',
              }}>
                ✦ Mark as Integrated
              </button>
            )}
            {state === 'integrated' && (
              <div style={{
                display: 'flex', alignItems: 'center', gap: 7,
                padding: '10px 18px',
                background: `${chamber.color}08`,
                border: `1px solid ${chamber.color}25`,
                borderRadius: 8,
              }}>
                <motion.span animate={{ opacity: [0.5, 1, 0.5] }} transition={{ duration: 2.5, repeat: Infinity }}
                  style={{ color: chamber.color }}>✦</motion.span>
                <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 9, letterSpacing: '0.2em', textTransform: 'uppercase', color: `${chamber.color}70` }}>
                  Integrated
                </span>
              </div>
            )}
          </div>

          {/* Related Codex */}
          <div style={{ borderTop: `1px solid ${chamber.color}12`, paddingTop: 24 }}>
            <ChamberCodexFeed chamber={chamber} />
          </div>

          {/* Bottom nav */}
          <div style={{ display: 'flex', gap: 12, marginTop: 48, paddingTop: 24, borderTop: '1px solid rgba(255,255,255,0.04)' }}>
            <button onClick={onPrev} style={{
              flex: 1, padding: '14px',
              background: 'rgba(255,255,255,0.02)',
              border: '1px solid rgba(255,255,255,0.06)',
              borderRadius: 10, color: 'rgba(232,232,232,0.4)',
              fontFamily: 'ui-monospace, monospace', fontSize: 9,
              letterSpacing: '0.2em', textTransform: 'uppercase', cursor: 'pointer',
            }}>
              ‹ Prev Chamber
            </button>
            <button onClick={onReturn} style={{
              flex: 1, padding: '14px',
              background: `${chamber.color}08`,
              border: `1px solid ${chamber.color}25`,
              borderRadius: 10, color: `${chamber.color}70`,
              fontFamily: 'ui-monospace, monospace', fontSize: 9,
              letterSpacing: '0.2em', textTransform: 'uppercase', cursor: 'pointer',
            }}>
              Return to Crystal
            </button>
            <button onClick={onNext} style={{
              flex: 1, padding: '14px',
              background: 'rgba(255,255,255,0.02)',
              border: '1px solid rgba(255,255,255,0.06)',
              borderRadius: 10, color: 'rgba(232,232,232,0.4)',
              fontFamily: 'ui-monospace, monospace', fontSize: 9,
              letterSpacing: '0.2em', textTransform: 'uppercase', cursor: 'pointer',
            }}>
              Next Chamber ›
            </button>
          </div>

        </div>
      </div>
    </motion.div>
  )
}

// ─── CRYSTAL GATEWAY ──────────────────────────────────────────────────────────

function CrystalGateway({
  states,
  onEnterChamber,
}: {
  states: Record<number, ChamberState>
  onEnterChamber: (num: number) => void
}) {
  const [hovered, setHovered] = useState<number | null>(null)
  const [ark, setArk] = useState<ArkDate | null>(null)
  const [pulse, setPulse] = useState('00')

  useEffect(() => {
    fetch(`${API_BASE}/api/ark-date`).then(r => r.ok ? r.json() : null).then(d => d && setArk(d)).catch(() => {})
    const t = setInterval(() => setPulse(String(new Date().getSeconds()).padStart(2,'0')), 1000)
    return () => clearInterval(t)
  }, [])

  const hoveredChamber = hovered !== null ? CHAMBERS[hovered - 1] : null

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', flexDirection: 'column',
      alignItems: 'center', background: '#020308',
    }}>

      {/* Minimal header */}
      <div style={{ width: '100%', padding: '22px 32px 0', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <p style={{ fontFamily: 'ui-monospace, monospace', fontSize: 7.5, letterSpacing: '0.5em', textTransform: 'uppercase', color: 'rgba(201,168,76,0.3)', margin: '0 0 4px' }}>
            Arkadia Nexus
          </p>
          <h1 style={{ fontFamily: 'serif', fontSize: 18, color: 'rgba(232,232,232,0.7)', margin: 0, letterSpacing: '0.12em', fontWeight: 400 }}>
            Encyclopedia Galactica
          </h1>
        </div>
        <div style={{ textAlign: 'right' }}>
          {ark && (
            <p style={{ fontFamily: 'ui-monospace, monospace', fontSize: 8, letterSpacing: '0.22em', color: 'rgba(0,212,170,0.45)', margin: '0 0 3px' }}>
              ◎ ARK Y{ark.ark_year} · D{ark.total_ark_day} · {ark.pulse}:{pulse}
            </p>
          )}
          <p style={{ fontFamily: 'ui-monospace, monospace', fontSize: 8, letterSpacing: '0.22em', color: 'rgba(201,168,76,0.25)', margin: 0 }}>
            12 Chambers · Echoes of the Lost Aeons
          </p>
        </div>
      </div>

      {/* Crystal matrix */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '20px 20px 0' }}>
        <div style={{ position: 'relative' }}>
          <svg
            viewBox="0 0 400 400"
            style={{ width: 'min(92vw, 480px)', height: 'min(92vw, 480px)', overflow: 'visible' }}
          >
            <defs>
              <radialGradient id="eg-void" cx="50%" cy="50%" r="50%">
                <stop offset="0%"   stopColor="#C9A84C" stopOpacity="0.025" />
                <stop offset="100%" stopColor="transparent" stopOpacity="0" />
              </radialGradient>
              <filter id="eg-glow">
                <feGaussianBlur stdDeviation="3.5" result="blur" />
                <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
              </filter>
              <filter id="eg-softglow">
                <feGaussianBlur stdDeviation="6" result="blur" />
                <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
              </filter>
            </defs>

            {/* Field void */}
            <circle cx={CX} cy={CY} r={190} fill="url(#eg-void)" />

            {/* Breathing group */}
            <motion.g
              animate={{ scale: [1, 1.018, 1], opacity: [0.88, 1, 0.88] }}
              transition={{ duration: 8, repeat: Infinity, ease: 'easeInOut' }}
              style={{ transformOrigin: `${CX}px ${CY}px` }}
            >
              {/* Guide ring */}
              <circle cx={CX} cy={CY} r={R} fill="none"
                stroke="rgba(201,168,76,0.06)" strokeWidth="0.6" strokeDasharray="4 12" />

              {/* Inner reference rings */}
              <circle cx={CX} cy={CY} r={R * 0.52} fill="none"
                stroke="rgba(201,168,76,0.03)" strokeWidth="0.4" strokeDasharray="2 8" />
              <circle cx={CX} cy={CY} r={R * 0.26} fill="none"
                stroke="rgba(201,168,76,0.03)" strokeWidth="0.3" />

              {/* Equilateral triangles (4 groups: 0,4,8 / 1,5,9 / 2,6,10 / 3,7,11) */}
              {[[0,4,8],[1,5,9],[2,6,10],[3,7,11]].map((grp, gi) =>
                grp.map((a, si) => {
                  const b = grp[(si + 1) % 3]
                  const [x1, y1] = nodeXY(a)
                  const [x2, y2] = nodeXY(b)
                  return <line key={`tri-${gi}-${si}`} x1={x1} y1={y1} x2={x2} y2={y2}
                    stroke="rgba(201,168,76,0.038)" strokeWidth="0.45" />
                })
              )}

              {/* Ring perimeter */}
              {CHAMBERS.map((_, i) => {
                const [x1, y1] = nodeXY(i)
                const [x2, y2] = nodeXY((i + 1) % 12)
                const isHovAdj = hovered !== null && (hovered - 1 === i || hovered - 1 === (i + 1) % 12)
                return (
                  <line key={`ring-${i}`} x1={x1} y1={y1} x2={x2} y2={y2}
                    stroke={isHovAdj ? 'rgba(201,168,76,0.2)' : 'rgba(201,168,76,0.07)'}
                    strokeWidth={isHovAdj ? 0.9 : 0.55}
                    style={{ transition: 'stroke 0.25s' }} />
                )
              })}

              {/* Spoke lines: center → each node */}
              {CHAMBERS.map((ch, i) => {
                const [x, y] = nodeXY(i)
                const isHov = hovered === ch.num
                return (
                  <motion.line key={`sp-${i}`} x1={CX} y1={CY} x2={x} y2={y}
                    stroke={isHov ? ch.color : 'rgba(201,168,76,0.045)'}
                    strokeWidth={isHov ? 0.9 : 0.4}
                    animate={isHov ? {} : { opacity: [0.045 / 0.045, 0.9, 0.045 / 0.045] }}
                    transition={{ duration: 5 + i * 0.3, repeat: Infinity, ease: 'easeInOut', delay: i * 0.35 }}
                    style={{ transition: 'stroke 0.25s' }}
                  />
                )
              })}

              {/* SOURCE FIELD center */}
              <motion.g
                animate={{ opacity: [0.55, 1, 0.55] }}
                transition={{ duration: 3.5, repeat: Infinity, ease: 'easeInOut' }}
              >
                <circle cx={CX} cy={CY} r={22} fill="rgba(201,168,76,0.06)"
                  stroke="rgba(201,168,76,0.28)" strokeWidth="0.8" filter="url(#eg-glow)" />
                <circle cx={CX} cy={CY} r={13} fill="rgba(201,168,76,0.08)"
                  stroke="rgba(201,168,76,0.15)" strokeWidth="0.5" />
                <text x={CX} y={CY - 1} textAnchor="middle" dominantBaseline="middle"
                  style={{ fontFamily: 'serif', fontSize: 9, fill: 'rgba(201,168,76,0.55)', userSelect: 'none' }}>
                  ☥
                </text>
                <text x={CX} y={CY + 33} textAnchor="middle"
                  style={{ fontFamily: 'ui-monospace, monospace', fontSize: 6.5, fill: 'rgba(201,168,76,0.25)', letterSpacing: 3, userSelect: 'none' }}>
                  SOURCE FIELD
                </text>
              </motion.g>

              {/* 12 chamber nodes */}
              {CHAMBERS.map((ch, i) => {
                const [x, y] = nodeXY(i)
                const st = states[ch.num] ?? 'dormant'
                const isHov = hovered === ch.num
                const lit = isHov

                // Diamond points
                const dw = 13, dh = 17
                const pts = `${x},${y - dh} ${x + dw},${y} ${x},${y + dh} ${x - dw},${y}`

                return (
                  <g key={ch.num}
                    onClick={() => onEnterChamber(ch.num)}
                    onMouseEnter={() => setHovered(ch.num)}
                    onMouseLeave={() => setHovered(null)}
                    style={{ cursor: 'pointer' }}
                  >
                    {/* Glow backdrop */}
                    {lit && (
                      <motion.circle cx={x} cy={y} r={28}
                        fill={`${ch.color}12`} stroke={`${ch.color}20`} strokeWidth="0.5"
                        filter="url(#eg-softglow)"
                        initial={{ scale: 0.8, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        exit={{ scale: 0.8, opacity: 0 }}
                      />
                    )}

                    {/* Integrated ring pulse */}
                    {st === 'integrated' && !lit && (
                      <motion.circle cx={x} cy={y} r={20}
                        fill="none" stroke={ch.color} strokeWidth="0.6"
                        animate={{ opacity: [0.2, 0.6, 0.2] }}
                        transition={{ duration: 3, repeat: Infinity, delay: i * 0.25, ease: 'easeInOut' }}
                      />
                    )}

                    {/* Node diamond */}
                    <polygon points={pts}
                      fill={lit ? `${ch.color}20` : st === 'integrated' ? `${ch.color}12` : st === 'explored' ? `${ch.color}08` : 'rgba(3,4,8,0.88)'}
                      stroke={lit ? ch.color : st === 'integrated' ? `${ch.color}70` : st === 'explored' ? `${ch.color}40` : 'rgba(255,255,255,0.09)'}
                      strokeWidth={lit ? 1.4 : st === 'integrated' ? 1.0 : 0.6}
                      filter={lit ? 'url(#eg-glow)' : undefined}
                      style={{ transition: 'all 0.22s' }}
                    />

                    {/* Chapter sigil */}
                    <text x={x} y={y + 1} textAnchor="middle" dominantBaseline="middle"
                      style={{
                        fontFamily: 'serif',
                        fontSize: lit ? 13 : 11,
                        fill: lit ? ch.color : st === 'integrated' ? `${ch.color}90` : st === 'explored' ? `${ch.color}65` : 'rgba(232,232,232,0.25)',
                        userSelect: 'none', transition: 'all 0.2s', pointerEvents: 'none',
                      }}>
                      {ch.sigil}
                    </text>

                    {/* State indicator (bottom of diamond) */}
                    {st !== 'dormant' && (
                      <text x={x} y={y + dh + 8} textAnchor="middle"
                        style={{ fontFamily: 'serif', fontSize: 6.5, fill: `${ch.color}55`, userSelect: 'none' }}>
                        {st === 'integrated' ? '✦' : '◈'}
                      </text>
                    )}
                  </g>
                )
              })}

            </motion.g>
          </svg>

          {/* Hover tooltip — HTML, positioned relative to container */}
          <AnimatePresence>
            {hoveredChamber && (
              <motion.div
                key={hoveredChamber.num}
                initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                transition={{ duration: 0.18 }}
                style={{
                  position: 'absolute', bottom: -8, left: '50%',
                  transform: 'translateX(-50%)',
                  pointerEvents: 'none', zIndex: 10, whiteSpace: 'nowrap',
                  textAlign: 'center',
                }}
              >
                <p style={{ fontFamily: 'serif', fontSize: 15, color: hoveredChamber.color, margin: '0 0 2px', letterSpacing: '0.04em' }}>
                  {hoveredChamber.chamberName}
                </p>
                <p style={{ fontFamily: 'ui-monospace, monospace', fontSize: 8.5, letterSpacing: '0.22em', textTransform: 'uppercase', color: `${hoveredChamber.color}65`, margin: 0 }}>
                  Chapter {ROMAN[hoveredChamber.num - 1]} · {hoveredChamber.chapterTitle}
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Idle prompt */}
        <AnimatePresence>
          {!hovered && (
            <motion.p
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              style={{
                fontFamily: 'ui-monospace, monospace', fontSize: 8.5,
                letterSpacing: '0.38em', textTransform: 'uppercase',
                color: 'rgba(201,168,76,0.2)', marginTop: 48,
                textAlign: 'center',
              }}
            >
              Select a chamber to enter
            </motion.p>
          )}
          {hovered && <div style={{ marginTop: 48, height: 20 }} />}
        </AnimatePresence>

        {/* Chamber state legend */}
        <div style={{ display: 'flex', gap: 20, marginTop: 32, marginBottom: 28, flexWrap: 'wrap', justifyContent: 'center' }}>
          {[['○ Dormant', 'rgba(232,232,232,0.18)'], ['◈ Explored', 'rgba(201,168,76,0.45)'], ['✦ Integrated', 'rgba(201,168,76,0.8)']].map(([label, color]) => (
            <span key={label} style={{ fontFamily: 'ui-monospace, monospace', fontSize: 8, letterSpacing: '0.18em', textTransform: 'uppercase', color }}>
              {label}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}

// ─── MAIN EXPORT ─────────────────────────────────────────────────────────────

export default function EncyclopediaGalactica() {
  const [states, setStates] = useState<Record<number, ChamberState>>(loadStates)
  const [reflections, setReflections] = useState<Record<number, string>>(loadReflections)
  const [activeChamber, setActiveChamber] = useState<number | null>(null)

  const enterChamber = useCallback((num: number) => {
    setActiveChamber(num)
    // Auto-mark as explored on first visit
    setStates(prev => {
      if (!prev[num] || prev[num] === 'dormant') {
        const next = { ...prev, [num]: 'explored' as ChamberState }
        saveStates(next)
        return next
      }
      return prev
    })
  }, [])

  const returnToCrystal = useCallback(() => setActiveChamber(null), [])

  const goNext = useCallback(() => {
    if (activeChamber === null) return
    const next = activeChamber === 12 ? 1 : activeChamber + 1
    enterChamber(next)
  }, [activeChamber, enterChamber])

  const goPrev = useCallback(() => {
    if (activeChamber === null) return
    const prev = activeChamber === 1 ? 12 : activeChamber - 1
    enterChamber(prev)
  }, [activeChamber, enterChamber])

  const markIntegrated = useCallback((num: number) => {
    setStates(prev => {
      const next = { ...prev, [num]: 'integrated' as ChamberState }
      saveStates(next)
      return next
    })
  }, [])

  const saveReflection = useCallback((num: number, text: string) => {
    setReflections(prev => {
      const next = { ...prev, [num]: text }
      saveReflections(next)
      return next
    })
  }, [])

  const chamber = activeChamber !== null ? CHAMBERS[activeChamber - 1] : null

  return (
    <>
      <CrystalGateway states={states} onEnterChamber={enterChamber} />

      <AnimatePresence>
        {chamber && (
          <ChamberView
            key={chamber.num}
            chamber={chamber}
            states={states}
            reflections={reflections}
            onReturn={returnToCrystal}
            onNext={goNext}
            onPrev={goPrev}
            onMarkIntegrated={markIntegrated}
            onSaveReflection={saveReflection}
          />
        )}
      </AnimatePresence>
    </>
  )
}
