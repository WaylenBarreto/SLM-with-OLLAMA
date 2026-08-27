import { StrictMode, useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

type Model = { name: string; size?: number; parameter_size?: string; quantization?: string };
type Hardware = { os: string; cpu: string; cores: number; threads: number; ram_gb: number; gpu?: string; vram_gb?: number; gpu_metrics_available: boolean; ollama_version?: string };
type Summary = { model: string; quality: number; avg_latency_seconds?: number; p95_latency_seconds?: number; tokens_per_second?: number; ram_used_mb?: number; failed_prompts: number };
type Run = { id: string; status: string; results: unknown[]; summary: Summary[] };

const API = 'http://127.0.0.1:8000/api';
const formatSize = (bytes?: number) => bytes ? `${(bytes / 1e9).toFixed(1)} GB` : 'n/a';

function App() {
  const [models, setModels] = useState<Model[]>([]);
  const [hardware, setHardware] = useState<Hardware | null>(null);
  const [online, setOnline] = useState(false);
  const [selected, setSelected] = useState<string[]>([]);
  const [repetitions, setRepetitions] = useState(1);
  const [run, setRun] = useState<Run | null>(null);
  const [message, setMessage] = useState('Ready to inspect your local runtime.');

  useEffect(() => {
    Promise.all([fetch(`${API}/models`), fetch(`${API}/hardware`), fetch(`${API}/health`)]).then(async ([modelResponse, hardwareResponse, healthResponse]) => {
      if (modelResponse.ok) { const available = await modelResponse.json(); setModels(available); setSelected(available.slice(0, 3).map((model: Model) => model.name)); }
      if (hardwareResponse.ok) setHardware(await hardwareResponse.json());
      if (healthResponse.ok) setOnline((await healthResponse.json()).ollama === 'available');
    }).catch(() => setMessage('Backend unavailable. Start FastAPI on port 8000.'));
  }, []);

  useEffect(() => {
    if (!run?.id || ['completed', 'failed'].includes(run.status)) return;
    const timer = window.setInterval(async () => {
      const response = await fetch(`${API}/runs/${run.id}`);
      if (response.ok) setRun(await response.json());
    }, 1000);
    return () => window.clearInterval(timer);
  }, [run?.id, run?.status]);

  const toggle = (name: string) => setSelected((current) => current.includes(name) ? current.filter((item) => item !== name) : [...current, name]);
  const startBenchmark = async () => {
    if (!selected.length) return setMessage('Select at least one installed model.');
    setMessage('Validating models and hardware snapshot...');
    const response = await fetch(`${API}/benchmarks`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ models: selected, repetitions }) });
    const data = await response.json();
    if (response.ok) {
      setRun({ id: data.run_id, status: 'running', results: [], summary: [] });
      setMessage(`Run ${data.run_id} is running. Results will update automatically.`);
    } else setMessage(data.detail || 'Unable to start benchmark.');
  };

  const download = (format: string) => run && window.open(`${API}/runs/${run.id}/export/${format}`, '_blank');

  return <div className="app-shell">
    <header className="topbar"><div><p className="eyebrow">LOCAL INFERENCE LAB / 01</p><h1>SLM Benchmark</h1></div><div className={`status ${online ? 'online' : ''}`}><span /> Ollama {online ? 'connected' : 'unavailable'}</div></header>
    <main>
      <section className="intro"><div><p className="eyebrow">CONTROL ROOM</p><h2>Measure the tradeoff.<br /><em>Keep the evidence.</em></h2><p className="lede">A reproducible test bench for local language models, using identical prompts and real measurements from this machine.</p></div><div className="runtime-note"><strong>DATA INTEGRITY</strong><span>No benchmark results are fabricated. Unavailable telemetry stays unavailable.</span></div></section>
      <section className="hardware-grid"><div className="section-label">HOST SNAPSHOT</div>{[['CPU', hardware?.cpu || 'Detecting...'], ['MEMORY', hardware ? `${hardware.ram_gb} GB RAM` : 'Detecting...'], ['GPU', hardware?.gpu || 'No telemetry'], ['RUNTIME', hardware?.ollama_version ? `Ollama ${hardware.ollama_version}` : 'Detecting...']].map(([label, value]) => <div className="metric" key={label}><span>{label}</span><strong>{value}</strong></div>)}</section>
      <section className="workspace"><div className="section-heading"><div><p className="eyebrow">BENCHMARK CONFIGURATION</p><h3>Choose your contenders</h3></div><span className="dataset">DATASET <b>CORE SUITE v1.0.0</b></span></div><div className="model-list">{models.map((model) => <button className={`model-row ${selected.includes(model.name) ? 'selected' : ''}`} onClick={() => toggle(model.name)} key={model.name}><span className="check">{selected.includes(model.name) ? '✓' : ''}</span><span className="model-name">{model.name}</span><span>{model.parameter_size || 'Parameter metadata pending'}</span><span>{model.quantization || 'Quantization metadata pending'}</span><span>{formatSize(model.size)}</span></button>)}</div>{!models.length && <div className="empty">No models detected. Confirm Ollama is running, then refresh the page.</div>}<div className="controls"><label>REPETITIONS <input type="number" min="1" max="20" value={repetitions} onChange={(event) => setRepetitions(Number(event.target.value))} /></label><label>TEMPERATURE <input type="number" value="0" readOnly /></label><button className="run-button" onClick={startBenchmark}>Run benchmark <span>→</span></button></div><p className="message">{message}</p></section>
      <section className="results"><div className="section-heading"><div><p className="eyebrow">RESULTS LEDGER</p><h3>{run ? `Run ${run.status}` : 'Waiting for measured evidence'}</h3></div>{run && <div className="exports"><button onClick={() => download('json')}>JSON</button><button onClick={() => download('csv')}>CSV</button><button onClick={() => download('markdown')}>MD</button></div>}</div>{run && run.summary.length ? <><div className="comparison-table"><div className="table-head"><span>MODEL</span><span>QUALITY</span><span>AVG LATENCY</span><span>P95 LATENCY</span><span>TOKENS / SEC</span><span>RAM</span></div>{run.summary.map((item) => <div className="table-row" key={item.model}><strong>{item.model}</strong><span className="quality">{item.quality}%</span><span>{item.avg_latency_seconds ?? 'n/a'}s</span><span>{item.p95_latency_seconds ?? 'n/a'}s</span><span>{item.tokens_per_second ?? 'n/a'}</span><span>{item.ram_used_mb ?? 'n/a'} MB</span></div>)}</div><div className="chart"><div className="chart-title">QUALITY / LATENCY</div>{run.summary.map((item) => <div className="bar-row" key={item.model}><span>{item.model}</span><div><i style={{ width: `${Math.min(item.quality, 100)}%` }} /></div><b>{item.quality}%</b></div>)}</div></> : <div className="empty results-empty"><div className="pulse">◎</div><p>{run ? `${run.results.length} prompt results collected so far.` : 'Your comparison table will appear here after a run.'}</p><small>Latency, throughput, quality, and resource metrics are collected per prompt and repetition.</small></div>}</section>
    </main><footer>LOCAL SLM BENCHMARK <span>•</span> Built for repeatable experiments on your hardware</footer>
  </div>;
}

createRoot(document.getElementById('root')!).render(<StrictMode><App /></StrictMode>);
