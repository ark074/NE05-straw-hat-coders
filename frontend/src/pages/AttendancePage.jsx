import React,{useState} from 'react';
import axios from 'axios';
export default function AttendancePage(){
  const [file,setFile]=useState(null); const API = import.meta.env.VITE_API_URL;
  const submit=async(e)=>{ e.preventDefault(); const fd=new FormData(); fd.append('file', file);
    const r = await axios.post(`${API}/recognize`, fd); alert(JSON.stringify(r.data.recorded || r.data.results, null, 2));
  }
  
  const downloadReport = async () => {
    try {
      const response = await fetch("http://localhost:8000/attendance_report");
      if (!response.ok) throw new Error("Failed to download report");

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "attendance_report.pdf";
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
      alert("Error downloading report");
    }
  };


  return (<div className="p-6"><h2 className="text-2xl mb-4">Mark Attendance</h2>
    <form onSubmit={submit} className="space-y-3">
      <input required type="file" accept="image/*" onChange={e=>setFile(e.target.files[0])} />
      <button className="px-4 py-2 bg-blue-600 text-white rounded">Recognize</button>
    </form><button onClick={downloadReport} className="bg-green-600 text-white px-4 py-2 rounded mt-4">
        Download Attendance Report (PDF)
      </button>
    </div>);
}