import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import HomePage from './pages/HomePage';
import EnrollPage from './pages/EnrollPage';
import AttendancePage from './pages/AttendancePage';
import LogsPage from './pages/LogsPage';
export default function App(){
  return (<Router>
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-gray-800 text-white p-4">
        <div className="max-w-6xl mx-auto flex gap-4">
          <Link to="/" className="font-semibold">Home</Link>
          <Link to="/enroll">Enroll</Link>
          <Link to="/attendance">Attendance</Link>
          <Link to="/logs">Logs</Link>
        </div>
      </nav>
      <main className="max-w-6xl mx-auto p-4">
        <Routes>
          <Route path="/" element={<HomePage/>} />
          <Route path="/enroll" element={<EnrollPage/>} />
          <Route path="/attendance" element={<AttendancePage/>} />
          <Route path="/logs" element={<LogsPage/>} />
        </Routes>
      </main>
    </div>
  </Router>);
}