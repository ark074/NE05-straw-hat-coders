import React, {useState} from 'react';
import axios from 'axios';
export default function EnrollPage(){
  const [name,setName]=useState(''); const [file,setFile]=useState(null);
  const API = import.meta.env.VITE_API_URL;
  const submit=async(e)=>{ e.preventDefault();
    const fd=new FormData(); fd.append('student_id', name); fd.append('files', file);
    await axios.post(`${API}/enroll`, fd); alert('Enrolled '+name); setName(''); setFile(null);
  }
  return (<div className="p-6"><h2 className="text-2xl mb-4">Enroll Student</h2>
    <form onSubmit={submit} className="space-y-3">
      <input required value={name} onChange={e=>setName(e.target.value)} placeholder="Student ID" className="p-2 border rounded w-full"/>
      <input required type="file" accept="image/*" onChange={e=>setFile(e.target.files[0])} />
      <button className="px-4 py-2 bg-green-600 text-white rounded">Enroll</button>
    </form></div>);
}