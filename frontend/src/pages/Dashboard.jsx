import React, {useRef, useState, useEffect} from "react";
import axios from "axios";

export default function Dashboard(){
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [streaming, setStreaming] = useState(false);
  const [attendance, setAttendance] = useState([]);
  const [enrollModal, setEnrollModal] = useState(false);
  const [studentId, setStudentId] = useState("");
  const [status, setStatus] = useState("");

  useEffect(()=>{
    async function start(){ 
      try{
        const s = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        videoRef.current.srcObject = s;
        await videoRef.current.play();
        setStreaming(true);
      }catch(e){ console.error(e); setStatus("Camera permission denied") }
    }
    start();
    fetchAttendance();
    return ()=>{ if(videoRef.current && videoRef.current.srcObject){ videoRef.current.srcObject.getTracks().forEach(t=>t.stop()) } }
  },[]);

  async function fetchAttendance(){
    try{ const r = await axios.get("/api/attendance"); setAttendance(r.data) }catch(e){ console.error(e) }
  }

  function captureBlob(){
    const canvas = canvasRef.current;
    const video = videoRef.current;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video,0,0,canvas.width,canvas.height);
    return new Promise(res => canvas.toBlob(res, "image/jpeg", 0.9));
  }

  async function recognizeFrame(){
    setStatus("Recognizing...");
    const b = await captureBlob();
    const fd = new FormData();
    fd.append("file", b, "frame.jpg");
    try{
      const r = await axios.post("/api/recognize", fd, { headers: {'Content-Type':'multipart/form-data'} });
      setStatus("Done");
      if(r.data.recorded && r.data.recorded.length>0){ fetchAttendance() }
      alert(JSON.stringify(r.data.results,null,2))
    }catch(e){ setStatus("Error"); console.error(e) }
  }

  async function enroll(){
    if(!studentId){ alert("Enter student id"); return; }
    setStatus("Enrolling...");
    // capture 3 frames for enrollment
    const fd = new FormData();
    for(let i=0;i<3;i++){
      const b = await captureBlob();
      fd.append("files", b, `img${i}.jpg`);
    }
    fd.append("student_id", studentId);
    try{
      const r = await axios.post("/api/enroll", fd, { headers: {'Content-Type':'multipart/form-data'} });
      setStatus("Enrolled "+studentId);
      setEnrollModal(false);
      setStudentId("");
      fetchAttendance();
    }catch(e){ setStatus("Error enrolling"); console.error(e) }
  }

  return (<div className="min-h-screen p-6">
    <div className="max-w-4xl mx-auto bg-white rounded-xl shadow-md p-6">
      <h1 className="text-2xl font-bold mb-4">Attendance AI — Pro</h1>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <video ref={videoRef} className="w-full rounded-md bg-black"></video>
          <canvas ref={canvasRef} className="hidden"></canvas>
          <div className="mt-2 flex gap-2">
            <button onClick={recognizeFrame} className="px-4 py-2 bg-blue-600 text-white rounded">Recognize</button>
            <button onClick={()=>setEnrollModal(true)} className="px-4 py-2 bg-green-600 text-white rounded">Enroll</button>
            <span className="ml-3 text-sm text-gray-600">{status}</span>
          </div>
        </div>
        <div>
          <h2 className="font-semibold">Recent Attendance</h2>
          <ul className="mt-2 space-y-2">
            {attendance.map(a=> <li key={a.id} className="p-2 border rounded">{a.student_id} — {new Date(a.timestamp).toLocaleString()}</li>)}
          </ul>
        </div>
      </div>
    </div>

    {enrollModal && <div className="fixed inset-0 flex items-center justify-center bg-black/40">
      <div className="bg-white p-6 rounded shadow-lg w-96">
        <h3 className="font-bold mb-2">Enroll Student</h3>
        <input value={studentId} onChange={e=>setStudentId(e.target.value)} className="w-full p-2 border rounded mb-2" placeholder="student id"/>
        <div className="flex justify-end gap-2">
          <button onClick={()=>setEnrollModal(false)} className="px-3 py-1 border rounded">Cancel</button>
          <button onClick={enroll} className="px-3 py-1 bg-green-600 text-white rounded">Enroll</button>
        </div>
      </div>
    </div>}

  </div>)
}