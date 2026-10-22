import React from 'react';
import { Activity, BookOpen, ClipboardList, FilePlus2, HeartPulse, LayoutDashboard, ShieldCheck, X } from 'lucide-react';
const items=[
  {id:'overview',label:'Home',icon:LayoutDashboard},
  {id:'new',label:'New prescription',icon:FilePlus2},
  {id:'library',label:'Prescriptions',icon:ClipboardList},
  {id:'research',label:'Model comparison',icon:BookOpen},
];
export default function Sidebar({active,onChange,count=0,opened,onClose}) {
 return <>
  {opened&&<button type="button" className="sidebar-backdrop" aria-label="Close menu" onClick={onClose}/>}
  <aside className={'sidebar'+(opened?' is-open':'')}>
   <div className="brand">
    <div className="brand-icon"><HeartPulse size={25}/></div>
    <div><div className="brand-word">MedSafe<span>AI</span></div><div className="brand-caption">PRESCRIPTION INTELLIGENCE</div></div>
    <button className="mobile-close icon-button" aria-label="Close navigation" onClick={onClose}><X size={18}/></button>
   </div>
   <div className="nav-caption">WORKSPACE</div>
   <nav aria-label="Primary navigation" className="side-nav">
    {items.map(({id,label,icon:Icon})=><button key={id} type="button" onClick={()=>onChange(id)}
      aria-current={active===id?'page':undefined} className={'side-link'+(active===id?' selected':'')}>
      <Icon size={19} strokeWidth={1.85}/><span>{label}</span>{id==='library'&&count>0&&<span className="side-count">{count}</span>}
    </button>)}
   </nav>
   <div className="side-bottom">
    <div className="safety-side-card">
     <div className="safety-heading"><ShieldCheck size={20}/> Human-led safety</div>
     <p>Check the original prescription before relying on the text.</p>
    </div>
    <div className="side-profile"><div className="profile-avatar"><Activity size={17}/></div><div><strong>MedSafe AI</strong><span>Local workspace</span></div></div>
   </div>
  </aside>
 </>;
}
