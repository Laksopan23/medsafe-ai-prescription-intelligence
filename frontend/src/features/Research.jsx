import React,{useState} from 'react';
import {BrainCircuit,CheckCircle2,Clock3} from 'lucide-react';
import OCRComparison from './OCRComparison.jsx';
import {Badge} from '../components/Status.jsx';

const readers=[
  ['tesseract','Tesseract','Standard text reader'],
  ['easyocr','EasyOCR','Handwriting reader'],
  ['paddleocr','PaddleOCR','Document reader'],
  ['craft_trocr','CRAFT + TrOCR','Fine-tuned handwriting reader'],
  ['gemini','Google-hosted text reader','Optional cloud reader'],
];
const targets=[
  ['Character error rate','10% or lower'],
  ['Medicine name accuracy','90% or higher'],
  ['Dose field accuracy','90% or higher'],
  ['Overdose precision and recall','85% or higher'],
  ['Age-check accuracy','85% or higher'],
  ['Processing time','10 seconds or less'],
];
const percent=value=>Number.isFinite(value)?(value*100).toFixed(2)+'%':'No result';
const displayName=name=>readers.find(([id])=>id===name)?.[1]||name;

export default function Research({models={},historical={},benchmarks={}}){
  const [selectedVariant,setSelectedVariant]=useState('original');
  const installed=models.benchmark_engines||{};
  const current=Object.entries(benchmarks.engines||{});
  const past=Object.entries(historical.engines||{});

  return <div className="stack-lg model-page">
    <section className="comparison-page-hero">
      <div className="comparison-page-icon"><BrainCircuit size={25}/></div>
      <div><h2>Compare text-reading methods</h2>
        <p>Choose one prescription image to see what each available method reads. Check the results against the original image.</p></div>
    </section>

    <section className="surface model-availability">
      <div className="section-top"><div><h3>Available methods</h3><p>Methods installed on this computer can be used in the comparison below.</p></div></div>
      <div className="model-cards">{readers.map(([id,name,description])=><div className="model-card" key={id}>
        <span className={'model-card-icon '+(installed[id]?'is-ready':'')}>
          {installed[id]?<CheckCircle2 size={20}/>:<Clock3 size={20}/>}</span>
        <div><strong>{name}</strong><p>{description}</p></div>
        <Badge tone={installed[id]?'teal':'amber'}>{installed[id]?'Ready':'Setup needed'}</Badge>
      </div>)}</div>
    </section>

    <OCRComparison/>

    <details className="surface model-evidence">
      <summary>{benchmarks.status==='HUMAN_VERIFIED_TEST'?'Independent test results':'Current test results'} <span>{current.length?'View measured results':'No test results loaded'}</span></summary>
      <div className="model-evidence-body">{current.length?<>
        <p>{benchmarks.status==='HUMAN_VERIFIED_TEST'?'These results come from a separately checked test set.':'These are development measurements, not an independent accuracy result.'} A blank score means it could not be measured.</p>
        <div className="table-scroll"><table className="data-table"><thead><tr>
          <th>Method</th><th>Images processed</th><th>Character error</th><th>Medicine name</th><th>Dose checks</th><th>Age checks</th><th>95th-percentile time</th>
        </tr></thead><tbody>{current.map(([name,item])=><tr key={name}>
          <td><strong>{displayName(name)}</strong></td>
          <td>{item.n_succeeded??'—'} / {item.n_total??'—'}</td>
          <td>{percent(item.metrics?.ocr?.CER)}</td>
          <td>{percent(item.metrics?.fields?.medicine?.accuracy)}</td>
          <td>{item.dose_alert_evaluated_n??'—'} / {item.n_total??'—'}</td>
          <td>{item.age_alert_evaluated_n??'—'} / {item.n_total??'—'}</td>
          <td>{item.timing?.p95_s!=null?item.timing.p95_s+' s':'—'}</td>
        </tr>)}</tbody></table></div>
      </>:<p>No independently checked test results have been loaded. The live comparison above still works for individual images when a method is installed.</p>}</div>
    </details>

    {past.length>0&&<details className="surface model-evidence">
      <summary>Earlier experiment results <span>{historical.n_aligned_images} medicine-word images</span></summary>
      <div className="model-evidence-body">
        <p>These older medicine-word measurements do not include the current fine-tuned model or prescription-level dose and age checks.</p>
        {historical.variants&&<label className="model-variant">Image condition <select aria-label="Earlier experiment image condition" value={selectedVariant} onChange={e=>setSelectedVariant(e.target.value)}>
          {Object.keys(historical.variants).map(v=><option key={v} value={v}>{v}</option>)}
        </select></label>}
        <div className="table-scroll"><table className="data-table"><thead><tr><th>Method</th><th>Character error</th><th>Word error</th><th>Medicine name</th></tr></thead>
          <tbody>{past.map(([name,item])=>{const variant=historical.variants?.[selectedVariant]?.[name]||{};
            return <tr key={name}><td><strong>{name==='trocr_historical'?'Earlier TrOCR':displayName(name)}</strong></td>
              <td>{percent(variant.CER??item.micro_CER)}</td>
              <td>{selectedVariant==='original'?percent(item.micro_WER):'No result'}</td>
              <td>{percent(variant.medicine_accuracy??item.medicine_accuracy)}</td></tr>})}</tbody></table></div>
      </div>
    </details>}

    <details className="surface model-evidence">
      <summary>About the measurements <span>How to interpret scores</span></summary>
      <div className="model-evidence-body"><p>The goals below are evaluation targets, not results. Accuracy claims require separate images with independently checked text and medication labels.</p>
        <div className="model-targets">{targets.map(([name,target])=><div key={name}><span>{name}</span><strong>{target}</strong></div>)}</div>
      </div>
    </details>
  </div>;
}
