"use strict";
// Browser-only simulation. Never reads or writes hospital backend records.
const labels = {1:"Critical",2:"High",3:"Medium",4:"Low"};
const initial = [{id:1,name:"Sample A",severity:3},{id:2,name:"Sample B",severity:1},{id:3,name:"Sample C",severity:4},{id:4,name:"Sample D",severity:2}];
let patients=[],served=0,nextId=1;
const el=id=>document.getElementById(id);
function reset(){patients=initial.map(p=>({...p}));served=0;nextId=5;el("message").textContent="Demo reset with fictional patients.";render()}
function render(){patients.sort((a,b)=>a.severity-b.severity||a.id-b.id);const tbody=el("queue");tbody.replaceChildren();for(const [i,p] of patients.entries()){const tr=document.createElement("tr");for(const value of [String(i+1),p.name,`${p.severity} — ${labels[p.severity]}`,String(p.id)]){const td=document.createElement("td");td.textContent=value;if(value===`${p.severity} — ${labels[p.severity]}`)td.className=`pill s${p.severity}`;tr.append(td)}tbody.append(tr)}if(!patients.length){const tr=document.createElement("tr"),td=document.createElement("td");td.colSpan=4;td.textContent="Queue empty — add a sample patient.";tr.append(td);tbody.append(tr)}el("waiting").textContent=patients.length;el("served").textContent=served}
el("patient-form").addEventListener("submit",e=>{e.preventDefault();const name=el("name").value.trim().slice(0,45);const severity=Number(el("severity").value);if(!name||![1,2,3,4].includes(severity))return;patients.push({id:nextId++,name,severity});el("patient-form").reset();el("message").textContent=`Added ${name} to demo queue.`;render()});
el("serve").addEventListener("click",()=>{if(!patients.length)return;patients.sort((a,b)=>a.severity-b.severity||a.id-b.id);const p=patients.shift();served++;el("message").textContent=`Served: ${p.name} (priority ${p.severity}).`;render()});el("reset").addEventListener("click",reset);reset();
