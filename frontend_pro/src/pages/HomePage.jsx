import React from 'react';
import { Link } from 'react-router-dom';
export default function HomePage(){
  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-4">AI Attendance System</h1>
      <p className="mb-4">Welcome — choose an action:</p>
      <ul className="space-y-2">
        <li><Link to="/enroll" className="text-blue-600">Enroll Student</Link></li>
        <li><Link to="/attendance" className="text-blue-600">Mark Attendance</Link></li>
        <li><Link to="/logs" className="text-blue-600">View Logs</Link></li>
      </ul>
    </div>
  );
}