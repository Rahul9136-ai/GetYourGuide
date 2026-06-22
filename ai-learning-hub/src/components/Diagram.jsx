// Reusable concept diagrams rendered inside lessons.
// Authored in Markdown with a fenced block:  ```diagram
//   neural-net | optional caption text
// ```
// Colors use the app's CSS variables so they match light/dark automatically.

const ARROW = 'var(--text-faint)'
const BORDER = 'var(--border)'
const ELEV = 'var(--bg-elev)'
const TEXT = 'var(--text)'
const DIM = 'var(--text-dim)'
const ACCENT = 'var(--accent)'
const ACCENT2 = 'var(--accent-2)'

// shared arrowhead marker
const Marker = ({ id, color = ARROW }) => (
  <marker id={id} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M1 1 L9 5 L1 9" fill="none" stroke={color} strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
  </marker>
)

const svgProps = (vb, max = 600) => ({
  viewBox: vb,
  width: '100%',
  xmlns: 'http://www.w3.org/2000/svg',
  style: { height: 'auto', maxWidth: max, display: 'block', margin: '0 auto', fontFamily: 'inherit' },
})

const T = (props) => <text fill={TEXT} fontSize="13" textAnchor="middle" {...props} />
const Td = (props) => <text fill={DIM} fontSize="11" textAnchor="middle" {...props} />
const Box = ({ x, y, w, h, accent, fill }) => (
  <rect x={x} y={y} width={w} height={h} rx="9"
        fill={fill || ELEV} stroke={accent ? ACCENT : BORDER} strokeWidth="1" />
)

/* ---------------- Diagrams ---------------- */

// Python — core data structures
function DataStructures() {
  const cards = [
    { c: 'list', a: '[ a, b, c ]', d: 'ordered • changeable' },
    { c: 'dict', a: '{ key: val }', d: 'lookup by key' },
    { c: 'tuple', a: '( x, y )', d: 'fixed • locked' },
    { c: 'set', a: '{ a, b }', d: 'unique items' },
  ]
  return (
    <svg {...svgProps('0 0 600 140')}>
      {cards.map((k, i) => {
        const x = 8 + i * 148, cx = x + 70
        return (
          <g key={i}>
            <Box x={x} y={14} w={140} h={112} />
            <T x={cx} y={46} fill={ACCENT2} fontSize="15" fontWeight="600">{k.c}</T>
            <T x={cx} y={78}>{k.a}</T>
            <Td x={cx} y={104}>{k.d}</Td>
          </g>
        )
      })}
    </svg>
  )
}

// ML — the core workflow loop
function MlWorkflow() {
  const steps = ['Data', 'Features', 'Model', 'Predict', 'Evaluate']
  const x = [6, 124, 242, 360, 478], w = 96
  return (
    <svg {...svgProps('0 0 600 170')}>
      <defs><Marker id="m-ml" /></defs>
      {steps.map((s, i) => (
        <g key={i}>
          <Box x={x[i]} y={28} w={w} h={54} accent={i === 2} />
          <T x={x[i] + w / 2} y={60}>{s}</T>
        </g>
      ))}
      {x.slice(0, 4).map((xi, i) => (
        <line key={i} x1={xi + w} y1={55} x2={x[i + 1]} y2={55} stroke={ARROW} strokeWidth="1.4" markerEnd="url(#m-ml)" />
      ))}
      <path d="M526 84 C 526 142 172 142 172 84" fill="none" stroke={ARROW} strokeWidth="1.4" strokeDasharray="5 5" markerEnd="url(#m-ml)" />
      <Td x={349} y={134}>improve &amp; repeat</Td>
    </svg>
  )
}

// DL — a neural network
function NeuralNet() {
  const inY = [80, 140, 200], h1Y = [50, 110, 170, 230], h2Y = [50, 110, 170, 230], outY = [140]
  const xIn = 70, xH1 = 230, xH2 = 390, xOut = 540, r = 14
  const node = (x, y, fill) => <circle cx={x} cy={y} r={r} fill={fill} stroke={BORDER} />
  const lines = []
  inY.forEach((a, i) => h1Y.forEach((b, j) => lines.push(<line key={`a${i}${j}`} x1={xIn + r} y1={a} x2={xH1 - r} y2={b} stroke={BORDER} strokeWidth="0.7" />)))
  h1Y.forEach((a, i) => h2Y.forEach((b, j) => lines.push(<line key={`b${i}${j}`} x1={xH1 + r} y1={a} x2={xH2 - r} y2={b} stroke={BORDER} strokeWidth="0.7" />)))
  h2Y.forEach((a, i) => outY.forEach((b, j) => lines.push(<line key={`c${i}${j}`} x1={xH2 + r} y1={a} x2={xOut - r} y2={b} stroke={BORDER} strokeWidth="0.7" />)))
  return (
    <svg {...svgProps('0 0 600 280')}>
      {lines}
      {inY.map((y, i) => <g key={`i${i}`}>{node(xIn, y, ACCENT2)}</g>)}
      {h1Y.map((y, i) => <g key={`h1${i}`}>{node(xH1, y, ELEV)}</g>)}
      {h2Y.map((y, i) => <g key={`h2${i}`}>{node(xH2, y, ELEV)}</g>)}
      {outY.map((y, i) => <g key={`o${i}`}>{node(xOut, y, ACCENT)}</g>)}
      <Td x={xIn} y={262}>Input</Td>
      <Td x={xH1} y={262}>Hidden</Td>
      <Td x={xH2} y={262}>Hidden</Td>
      <Td x={xOut} y={262}>Output</Td>
    </svg>
  )
}

// DL — the training loop
function TrainingLoop() {
  const cells = [
    { x: 40, y: 30, t: 'Forward', d: 'predict' },
    { x: 360, y: 30, t: 'Loss', d: 'measure error' },
    { x: 360, y: 130, t: 'Backprop', d: 'find blame' },
    { x: 40, y: 130, t: 'Update', d: 'adjust weights' },
  ]
  return (
    <svg {...svgProps('0 0 600 210')}>
      <defs><Marker id="m-tl" /></defs>
      {cells.map((c, i) => (
        <g key={i}>
          <Box x={c.x} y={c.y} w={160} h={50} accent />
          <T x={c.x + 80} y={c.y + 24} fontWeight="600">{c.t}</T>
          <Td x={c.x + 80} y={c.y + 41}>{c.d}</Td>
        </g>
      ))}
      <line x1={200} y1={55} x2={360} y2={55} stroke={ARROW} strokeWidth="1.4" markerEnd="url(#m-tl)" />
      <line x1={440} y1={80} x2={440} y2={130} stroke={ARROW} strokeWidth="1.4" markerEnd="url(#m-tl)" />
      <line x1={360} y1={155} x2={200} y2={155} stroke={ARROW} strokeWidth="1.4" markerEnd="url(#m-tl)" />
      <line x1={120} y1={130} x2={120} y2={80} stroke={ARROW} strokeWidth="1.4" markerEnd="url(#m-tl)" />
      <Td x={280} y={108}>repeat every epoch</Td>
    </svg>
  )
}

// GenAI — embeddings cluster meaning by closeness
function Embeddings() {
  return (
    <svg {...svgProps('0 0 600 250')}>
      <rect x="14" y="14" width="572" height="210" rx="12" fill="none" stroke={BORDER} strokeDasharray="4 5" />
      <circle cx="180" cy="95" r="80" fill={ACCENT} opacity="0.08" />
      <circle cx="170" cy="80" r="6" fill={ACCENT2} />
      <text x="186" y="84" fill={TEXT} fontSize="12">"refund policy"</text>
      <circle cx="205" cy="120" r="6" fill={ACCENT2} />
      <text x="221" y="124" fill={TEXT} fontSize="12">"how to get money back"</text>
      <circle cx="470" cy="185" r="6" fill={DIM} />
      <text x="358" y="189" fill={DIM} fontSize="12">"today's weather"</text>
      <Td x={180} y={200} fill={ACCENT2}>similar meaning → close together</Td>
    </svg>
  )
}

// GenAI — the RAG pipeline
function RagPipeline() {
  const row1 = [
    { x: 10, t: 'Question', d: 'user asks' },
    { x: 210, t: 'Embed', d: 'text → vector' },
    { x: 410, t: 'Search DB', d: 'find similar' },
  ]
  const row2 = [
    { x: 10, t: 'Build prompt', d: 'context + question' },
    { x: 210, t: 'LLM', d: 'grounded answer' },
    { x: 410, t: 'Answer', d: 'with sources' },
  ]
  const w = 180, h = 50
  return (
    <svg {...svgProps('0 0 600 200')}>
      <defs><Marker id="m-rag" /></defs>
      {row1.map((c, i) => (
        <g key={`r1${i}`}>
          <Box x={c.x} y={28} w={w} h={h} accent={i === 2} />
          <T x={c.x + w / 2} y={50} fontWeight="600">{c.t}</T>
          <Td x={c.x + w / 2} y={67}>{c.d}</Td>
        </g>
      ))}
      {row2.map((c, i) => (
        <g key={`r2${i}`}>
          <Box x={c.x} y={128} w={w} h={h} accent={i === 1} />
          <T x={c.x + w / 2} y={150} fontWeight="600">{c.t}</T>
          <Td x={c.x + w / 2} y={167}>{c.d}</Td>
        </g>
      ))}
      <line x1={190} y1={53} x2={210} y2={53} stroke={ARROW} strokeWidth="1.4" markerEnd="url(#m-rag)" />
      <line x1={390} y1={53} x2={410} y2={53} stroke={ARROW} strokeWidth="1.4" markerEnd="url(#m-rag)" />
      <path d="M500 78 L500 103 L100 103 L100 128" fill="none" stroke={ARROW} strokeWidth="1.4" markerEnd="url(#m-rag)" />
      <line x1={190} y1={153} x2={210} y2={153} stroke={ARROW} strokeWidth="1.4" markerEnd="url(#m-rag)" />
      <line x1={390} y1={153} x2={410} y2={153} stroke={ARROW} strokeWidth="1.4" markerEnd="url(#m-rag)" />
    </svg>
  )
}

// Agents — the reason/act loop
function AgentLoop() {
  const steps = [
    { x: 10, t: 'Goal' },
    { x: 145, t: 'Think' },
    { x: 295, t: 'Act' },
    { x: 445, t: 'Observe' },
  ]
  const w = 120
  return (
    <svg {...svgProps('0 0 600 230')}>
      <defs><Marker id="m-ag" /></defs>
      {steps.map((s, i) => (
        <g key={i}>
          <Box x={s.x} y={80} w={w} h={50} accent={i === 0} />
          <T x={s.x + w / 2} y={110} fontWeight="600">{s.t}</T>
        </g>
      ))}
      <line x1={130} y1={105} x2={145} y2={105} stroke={ARROW} strokeWidth="1.4" markerEnd="url(#m-ag)" />
      <line x1={265} y1={105} x2={295} y2={105} stroke={ARROW} strokeWidth="1.4" markerEnd="url(#m-ag)" />
      <line x1={415} y1={105} x2={445} y2={105} stroke={ARROW} strokeWidth="1.4" markerEnd="url(#m-ag)" />
      <path d="M505 80 C 505 22 205 22 205 80" fill="none" stroke={ARROW} strokeWidth="1.4" markerEnd="url(#m-ag)" />
      <Td x={355} y={28}>loop until done</Td>
      <Box x={445} y={160} w={120} h={44} />
      <T x={505} y={187} fontWeight="600">Answer</T>
      <line x1={505} y1={130} x2={505} y2={160} stroke={ARROW} strokeWidth="1.4" markerEnd="url(#m-ag)" />
      <Td x={556} y={150} fill={DIM}>done</Td>
    </svg>
  )
}

// Agentic — coordinator + specialists
function Coordinator() {
  const specs = [
    { x: 40, t: 'Researcher', d: 'gathers facts' },
    { x: 225, t: 'Writer', d: 'drafts' },
    { x: 410, t: 'Editor', d: 'reviews' },
  ]
  return (
    <svg {...svgProps('0 0 600 200')}>
      <defs><Marker id="m-co" /></defs>
      <Box x={220} y={18} w={160} h={50} accent />
      <T x={300} y={42} fontWeight="600">Coordinator</T>
      <Td x={300} y={59}>plans &amp; delegates</Td>
      {specs.map((s, i) => (
        <g key={i}>
          <Box x={s.x} y={130} w={150} h={50} />
          <T x={s.x + 75} y={154} fontWeight="600">{s.t}</T>
          <Td x={s.x + 75} y={171}>{s.d}</Td>
          <line x1={300} y1={68} x2={s.x + 75} y2={130} stroke={ARROW} strokeWidth="1.3" markerEnd="url(#m-co)" />
        </g>
      ))}
    </svg>
  )
}

// Cloud — the four core resources
function CloudResources() {
  const cards = [
    { c: 'Compute', d: 'runs your code' },
    { c: 'Storage', d: 'keeps files & data' },
    { c: 'Networking', d: 'routes traffic' },
    { c: 'Identity', d: 'who can access' },
  ]
  return (
    <svg {...svgProps('0 0 600 130')}>
      {cards.map((k, i) => {
        const x = 8 + i * 148, cx = x + 70
        return (
          <g key={i}>
            <Box x={x} y={14} w={140} h={100} />
            <T x={cx} y={56} fill={ACCENT2} fontSize="14" fontWeight="600">{k.c}</T>
            <Td x={cx} y={84}>{k.d}</Td>
          </g>
        )
      })}
    </svg>
  )
}

// Cloud — the CI/CD pipeline
function CICD() {
  const steps = ['git push', 'Test', 'Build', 'Deploy', 'Live']
  const x = [6, 124, 242, 360, 478], w = 96
  return (
    <svg {...svgProps('0 0 600 175')}>
      <defs><Marker id="m-ci" /></defs>
      {steps.map((s, i) => (
        <g key={i}>
          <Box x={x[i]} y={28} w={w} h={50} accent={i === 4} />
          <T x={x[i] + w / 2} y={58}>{s}</T>
        </g>
      ))}
      {x.slice(0, 4).map((xi, i) => (
        <line key={i} x1={xi + w} y1={53} x2={x[i + 1]} y2={53} stroke={ARROW} strokeWidth="1.4" markerEnd="url(#m-ci)" />
      ))}
      <path d="M176 78 L176 120 L300 120" fill="none" stroke={ARROW} strokeWidth="1.3" strokeDasharray="5 5" markerEnd="url(#m-ci)" />
      <text x={310} y={124} fill={DIM} fontSize="11">if tests fail → stop &amp; report</text>
    </svg>
  )
}

const REGISTRY = {
  'data-structures': DataStructures,
  'ml-workflow': MlWorkflow,
  'neural-net': NeuralNet,
  'training-loop': TrainingLoop,
  'embeddings': Embeddings,
  'rag-pipeline': RagPipeline,
  'agent-loop': AgentLoop,
  'coordinator': Coordinator,
  'cloud-resources': CloudResources,
  'cicd': CICD,
}

export default function Diagram({ spec }) {
  const raw = String(spec || '').trim()
  const [namePart, ...capParts] = raw.split('|')
  const name = namePart.trim()
  const caption = capParts.join('|').trim()
  const Cmp = REGISTRY[name]

  return (
    <div className="lesson-diagram">
      {Cmp ? <Cmp /> : <div className="diagram-missing">[diagram: {name}]</div>}
      {caption && <div className="diagram-cap">{caption}</div>}
    </div>
  )
}
