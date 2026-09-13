import { ArrowRight, Check, ChevronDown, FileImage, Plus, ShieldCheck, Sparkles, Trash2, Trophy, UploadCloud } from 'lucide-react'
import { useRef, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './styles.css'

const API_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')

const initialRows = [
    { team: 'CSK', played: 12, wins: 6, losses: 6, no_results: 0, points: 12, nrr: 0.321 },
    { team: 'GT', played: 12, wins: 8, losses: 4, no_results: 0, points: 16, nrr: 0.612 },
    { team: 'RCB', played: 12, wins: 9, losses: 3, no_results: 0, points: 18, nrr: 1.052 },
    { team: 'MI', played: 12, wins: 6, losses: 6, no_results: 0, points: 12, nrr: -0.114 },
]

function App() {
    const [rows, setRows] = useState(initialRows)
    const [fixtures, setFixtures] = useState([{ team_a: 'CSK', team_b: 'GT' }, { team_a: 'CSK', team_b: 'MI' }, { team_a: 'GT', team_b: 'MI' }])
    const [selectedTeam, setSelectedTeam] = useState('CSK')
    const [step, setStep] = useState('upload')
    const [result, setResult] = useState(null)
    const [uploadError, setUploadError] = useState('')
    const [uploading, setUploading] = useState(false)
    const [analysisError, setAnalysisError] = useState('')
    const fileInputRef = useRef(null)

    const updateRow = (index, field, value) => setRows(rows.map((row, rowIndex) => rowIndex === index ? { ...row, [field]: field === 'team' ? value : Number(value) } : row))
    const addFixture = () => setFixtures([...fixtures, { team_a: 'CSK', team_b: 'RCB' }])
    const removeFixture = (index) => setFixtures(fixtures.filter((_, fixtureIndex) => fixtureIndex !== index))
    const updateFixture = (index, field, value) => setFixtures(fixtures.map((fixture, fixtureIndex) => fixtureIndex === index ? { ...fixture, [field]: value } : fixture))

    const uploadScoreboard = async (file) => {
        if (!file) return
        setUploadError('')
        setUploading(true)
        try {
            const formData = new FormData()
            formData.append('file', file)
            const response = await fetch(`${API_URL}/api/scoreboard/extract`, { method: 'POST', body: formData })
            const payload = await response.json()
            if (!response.ok) throw new Error(payload.detail || 'The scoreboard could not be uploaded.')
            if (payload.rows?.length) setRows(payload.rows)
            setStep('verify')
        } catch (error) {
            setUploadError(error.message || 'Upload failed. Please try another file.')
        } finally {
            setUploading(false)
        }
    }

    const runAnalysis = async () => {
        setAnalysisError('')
        try {
            const response = await fetch(`${API_URL}/api/qualification/analyze`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ season: 2026, selected_team: selectedTeam, standings: rows, remaining_matches: fixtures }) })
            const payload = await response.json()
            if (!response.ok) throw new Error(payload.detail || 'The qualification analysis failed.')
            setResult(payload)
        } catch (error) {
            setAnalysisError(error.message || 'The qualification analysis failed.')
            return
        }
        setStep('analysis')
    }

    return <div className="app-shell">
        <header className="topbar"><div className="brand"><span className="brand-mark"><Trophy size={18} /></span><span>IPL<span className="brand-accent">/</span>QUALIFY</span></div><div className="season-pill"><span className="live-dot" /> 2026 season <ChevronDown size={15} /></div></header>
        <main>
            <section className="hero"><div className="eyebrow"><Sparkles size={14} /> DETERMINISTIC PLAYOFF INTELLIGENCE</div><h1>Know the path.<br /><em>Not just the hope.</em></h1><p className="hero-copy">Upload a points table, verify the numbers, and map every possible road to the playoffs.</p><div className="stepper">{['Upload', 'Verify', 'Analyze'].map((label, index) => <div className={`step ${step === ['upload', 'verify', 'analysis'][index] ? 'active' : ''}`} key={label}><span>{String(index + 1).padStart(2, '0')}</span>{label}</div>)}</div></section>
            {step === 'upload' && <section className="upload-panel" onClick={() => fileInputRef.current?.click()} onDragOver={event => event.preventDefault()} onDrop={event => { event.preventDefault(); uploadScoreboard(event.dataTransfer.files[0]) }}><div className="upload-icon"><UploadCloud size={28} /></div><h2>{uploading ? 'Reading scoreboard...' : 'Upload IPL points table'}</h2><p>Drop an image here or choose a file from your device.</p><span className="file-types">PNG · JPG · WEBP · PDF <ArrowRight size={14} /></span>{uploadError && <div className="upload-error">{uploadError}</div>}<input ref={fileInputRef} type="file" accept="image/png,image/jpeg,image/webp,application/pdf" onClick={event => event.stopPropagation()} onChange={event => uploadScoreboard(event.target.files[0])} /></section>}
            {step === 'verify' && <section className="workspace"><div className="section-heading"><div><div className="eyebrow">02 / VERIFY DATA</div><h2>Make the table yours.</h2><p>OCR is a first pass. Confirm every figure before the engine touches it.</p></div><div className="confidence"><ShieldCheck size={17} /> Review required</div></div><div className="table-wrap"><table><thead><tr><th>Team</th><th>MP</th><th>W</th><th>L</th><th>NR</th><th>PTS</th><th>NRR</th><th /></tr></thead><tbody>{rows.map((row, index) => <tr key={index}>{['team', 'played', 'wins', 'losses', 'no_results', 'points', 'nrr'].map(field => <td key={field}><input className={field === 'team' ? 'team-input' : ''} value={row[field]} onChange={event => updateRow(index, field, event.target.value)} /></td>)}<td><button className="icon-button" title="Remove team" onClick={() => setRows(rows.filter((_, rowIndex) => rowIndex !== index))}><Trash2 size={15} /></button></td></tr>)}</tbody></table></div><div className="fixtures-block"><div className="subheading"><div><span className="eyebrow">REMAINING FIXTURES</span><h3>What is still to play?</h3></div><button className="text-button" onClick={addFixture}><Plus size={16} /> Add match</button></div>{fixtures.map((fixture, index) => <div className="fixture-row" key={index}><span className="fixture-number">{String(index + 1).padStart(2, '0')}</span><select value={fixture.team_a} onChange={event => updateFixture(index, 'team_a', event.target.value)}>{rows.map(row => <option key={row.team}>{row.team}</option>)}</select><span>vs</span><select value={fixture.team_b} onChange={event => updateFixture(index, 'team_b', event.target.value)}>{rows.map(row => <option key={row.team}>{row.team}</option>)}</select><button className="icon-button" onClick={() => removeFixture(index)}><Trash2 size={15} /></button></div>)}</div><div className="confirm-row"><label className="team-select">Analyze <select value={selectedTeam} onChange={event => setSelectedTeam(event.target.value)}>{rows.map(row => <option key={row.team}>{row.team}</option>)}</select> <ChevronDown size={15} /></label><button className="primary-button" onClick={runAnalysis}>Run qualification engine <ArrowRight size={17} /></button></div></section>}
            {step === 'analysis' && result && <section className="analysis"><div className={`status-banner ${result.status.toLowerCase()}`}><div><div className="eyebrow">QUALIFICATION STATUS</div><h2>{result.selected_team}: {result.status}</h2><p>{result.explanation}</p></div><div className="status-icon"><Check size={28} /></div></div><div className="metrics"><Metric label="Current points" value={result.current_points} /><Metric label="Maximum possible" value={result.maximum_points} accent /><Metric label="Best position" value={`#${result.best_position}`} /><Metric label="Worst position" value={`#${result.worst_position}`} /></div><div className="analysis-grid"><div className="conditions"><div className="eyebrow">THE MATH</div><h3>What needs to happen</h3><div className="condition"><span className="condition-check">✓</span><span>Win the remaining matches involving {result.selected_team}</span><strong>{result.matches_remaining} / {result.matches_remaining}</strong></div><div className="condition"><span className="condition-check">✓</span><span>Stay inside the top four after all results</span><strong>TOP 4</strong></div><div className="condition"><span className="condition-check">!</span><span>Future NRR may decide tied points</span><strong>{result.nrr_dependency ? 'YES' : 'NO'}</strong></div></div><div className="scenario-card"><div className="eyebrow">SCENARIO UNIVERSE</div><div className="scenario-number">{result.scenarios_analyzed}</div><p>possible match-outcome combinations analyzed</p><div className="bar"><span style={{ width: result.scenarios_analyzed ? `${(result.qualifying_scenarios / result.scenarios_analyzed) * 100}%` : '0%' }} /></div><div className="scenario-split"><span><b>{result.qualifying_scenarios}</b> qualify</span><span><b>{result.elimination_scenarios}</b> eliminated</span></div></div></div>{result.warnings?.map(warning => <div className="warning" key={warning}><FileImage size={16} /> {warning}</div>)}<button className="secondary-button" onClick={() => setStep('verify')}>Edit verified data</button></section>}
        </main>{analysisError && <div className="warning analysis-error">{analysisError}</div>}<footer><span>IPL / QUALIFY</span><span>Decisions from rules, not guesses.</span></footer>
    </div>
}

function Metric({ label, value, accent }) { return <div className={`metric ${accent ? 'accent' : ''}`}><span>{label}</span><strong>{value}</strong></div> }

createRoot(document.getElementById('root')).render(<App />)
