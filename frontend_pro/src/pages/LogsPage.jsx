import React, {useEffect,useState} from 'react';
import axios from 'axios';
export default function LogsPage(){
  const [logs,setLogs]=useState([]); const API = import.meta.env.VITE_API_URL;
  useEffect(()=>{ axios.get(`${API}/attendance`).then(r=>setLogs(r.data)).catch(()=>setLogs([])); },[]);
  return (<div className="p-6"><h2 className="text-2xl mb-4">Attendance Logs</h2>
    <ul className="space-y-2">{logs.map(l=> <li key={l.id} className="p-2 border rounded">{l.student_id} — {new Date(l.timestamp).toLocaleString()}</li>)}</ul>
  </div>);
}