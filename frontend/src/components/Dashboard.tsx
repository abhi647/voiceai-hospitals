"use client";

import { useState, useEffect } from "react";
import TranscriptModal from "./TranscriptModal";

interface Stats {
  total_calls: number;
  escalated_calls: number;
  active_calls: number;
  total_appointments: number;
}

interface Call {
  id: number;
  call_id: string;
  start_time: string;
  status: string;
  intent: string;
  urgency_score: number;
}

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [recentCalls, setRecentCalls] = useState<Call[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSessionId, setSelectedSessionId] = useState<number | null>(null);

  const fetchData = async () => {
    try {
      const [statsRes, callsRes] = await Promise.all([
        fetch("http://localhost:8000/dashboard/stats"),
        fetch("http://localhost:8000/dashboard/recent-calls")
      ]);
      
      if (statsRes.ok) setStats(await statsRes.json());
      if (callsRes.ok) setRecentCalls(await callsRes.json());
    } catch (err) {
      console.error("Dashboard fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000); // Refresh every 5s
    return () => clearInterval(interval);
  }, []);

  if (loading && !stats) return <div className="text-center p-8 text-gray-400">Loading Dashboard...</div>;

  return (
    <div className="w-full space-y-8 animate-in fade-in duration-500">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard title="Total Calls" value={stats?.total_calls || 0} color="bg-blue-600" />
        <StatCard title="Active Sessions" value={stats?.active_calls || 0} color="bg-green-500" pulse={!!stats?.active_calls && stats.active_calls > 0} />
        <StatCard title="Escalations" value={stats?.escalated_calls || 0} color="bg-red-500" />
        <StatCard title="Appointments" value={stats?.total_appointments || 0} color="bg-purple-500" />
      </div>

      {/* Recent Calls Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
          <div>
            <h3 className="font-semibold text-gray-800">Recent Calls</h3>
            <p className="text-xs text-gray-500">Live feed of patient interactions</p>
          </div>
          <button onClick={fetchData} className="text-xs bg-white border border-gray-200 px-3 py-1.5 rounded-md text-gray-600 hover:bg-gray-50 transition-colors shadow-sm">
            Refresh
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-gray-500 font-medium border-b border-gray-100">
              <tr>
                <th className="px-6 py-3">Time</th>
                <th className="px-6 py-3">Call Reference</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3">Urgency</th>
                <th className="px-6 py-3">Inferred Intent</th>
                <th className="px-6 py-3">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 italic">
              {recentCalls.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-gray-400 bg-gray-50/50">
                    <div className="flex flex-col items-center">
                      <svg className="w-8 h-8 mb-2 opacity-20" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>
                      No calls recorded yet. Speak to the assistant to see data.
                    </div>
                  </td>
                </tr>
              ) : (
                recentCalls.map((call) => (
                  <tr key={call.id} className="hover:bg-gray-50 transition-colors group">
                    <td className="px-6 py-4 text-gray-600 whitespace-nowrap">
                      {new Date(call.start_time).toLocaleTimeString([], { hour12: true, hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td className="px-6 py-4 font-mono text-[10px] text-gray-400 truncate max-w-[120px]">{call.call_id}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold tracking-wide uppercase ${
                        call.status === 'escalated' ? 'bg-red-50 text-red-600 border border-red-100' : 
                        call.status === 'active' ? 'bg-green-50 text-green-600 border border-green-100' : 'bg-gray-100 text-gray-600'
                      }`}>
                        {call.status}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                       <UrgencyDot score={call.urgency_score} />
                    </td>
                    <td className="px-6 py-4 text-gray-700 capitalize font-medium">
                      {call.intent || "Identifying..."}
                    </td>
                    <td className="px-6 py-4">
                      <button 
                        onClick={() => setSelectedSessionId(call.id)}
                        className="text-blue-600 hover:text-blue-800 font-semibold text-xs flex items-center group-hover:underline"
                      >
                         View Transcript
                         <svg className="w-3 h-3 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {selectedSessionId && (
        <TranscriptModal 
          sessionId={selectedSessionId} 
          onClose={() => setSelectedSessionId(null)} 
        />
      )}
    </div>
  );
}

function StatCard({ title, value, color, pulse = false }: { title: string, value: number, color: string, pulse?: boolean }) {
  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
      <div className="flex justify-between items-start">
        <p className="text-sm font-medium text-gray-500">{title}</p>
        {pulse && <span className="flex h-2 w-2 rounded-full bg-red-400 animate-ping"></span>}
      </div>
      <p className={`text-3xl font-bold mt-2 text-gray-800`}>{value}</p>
      <div className={`h-1 w-full mt-4 rounded-full ${color} opacity-20`}></div>
    </div>
  );
}

function UrgencyDot({ score }: { score: number }) {
  const color = score > 7 ? 'bg-red-500' : score > 4 ? 'bg-yellow-500' : 'bg-green-500';
  return (
    <div className="flex items-center space-x-2">
      <div className={`w-2 h-2 rounded-full ${color}`}></div>
      <span className="text-gray-600">{score}/10</span>
    </div>
  );
}
