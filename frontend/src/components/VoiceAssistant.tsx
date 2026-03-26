"use client";

import { useState } from "react";
import {
  LiveKitRoom,
  RoomAudioRenderer,
  VoiceAssistantControlBar,
  useVoiceAssistant,
  useConnectionState,
} from "@livekit/components-react";
import { ConnectionState } from "livekit-client";
import "@livekit/components-styles";

export default function VoiceAssistant() {
  const [token, setToken] = useState("");
  const [serverUrl, setServerUrl] = useState("");
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState("");

  const connectToVoiceAgent = async () => {
    setIsConnecting(true);
    setError("");
    try {
      const participantName = `patient-${Math.floor(Math.random() * 10000)}`;
      
      const response = await fetch("http://127.0.0.1:8000/voice/token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ participant_name: participantName }),
      });
      
      if (!response.ok) {
        throw new Error(`Token request failed: ${response.status}`);
      }
      
      const data = await response.json();
      console.log("Token received:", data.token?.substring(0, 20) + "...");
      console.log("Room:", data.room_name);
      setToken(data.token);
      setServerUrl(process.env.NEXT_PUBLIC_LIVEKIT_URL || "wss://hospital-voice-ai-d76a5vz4.livekit.cloud");
      
    } catch (err: any) {
      console.error("Failed to connect", err);
      setError(err.message || "Connection failed");
    } finally {
      setIsConnecting(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center p-8 bg-gray-50 border border-gray-200 rounded-2xl shadow-sm text-black w-full max-w-md mx-auto">
      <h2 className="text-2xl font-semibold mb-6">Hospital Front Desk AI</h2>
      
      {error && (
        <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-lg text-sm">{error}</div>
      )}
      
      {!token ? (
        <button 
          onClick={connectToVoiceAgent}
          disabled={isConnecting}
          className="px-6 py-3 bg-blue-600 text-white font-medium rounded-full hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          {isConnecting ? "Connecting..." : "Tap to Speak with AI"}
        </button>
      ) : (
        <LiveKitRoom
          token={token}
          serverUrl={serverUrl}
          connect={true}
          audio={false}
          video={false}
          onDisconnected={() => console.log("LiveKit disconnected")}
          onError={(e) => {
            console.error("LiveKit error:", e);
            setError(String(e));
          }}
          className="flex flex-col items-center w-full"
        >
          <AgentVisualizer />
          <div className="mt-8">
            <VoiceAssistantControlBar />
          </div>
          <RoomAudioRenderer />
        </LiveKitRoom>
      )}
    </div>
  );
}

function AgentVisualizer() {
  const voiceAssistant = useVoiceAssistant();
  const { state, audioTrack } = voiceAssistant;
  const roomState = useConnectionState();

  // Debug: log all state values
  console.log("Room state:", roomState, "| Agent state:", state, "| Audio track:", !!audioTrack);

  if (roomState !== ConnectionState.Connected) {
    return (
      <div className="flex flex-col items-center">
        <div className="w-32 h-32 rounded-full bg-yellow-100 flex items-center justify-center animate-pulse">
          <div className="w-24 h-24 rounded-full bg-yellow-400 flex items-center justify-center">
            <svg className="w-10 h-10 text-white animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
        </div>
        <p className="mt-4 font-medium text-yellow-600">
          Connecting to room... ({roomState})
        </p>
      </div>
    );
  }

  // Map all possible states to UI
  const getStateInfo = () => {
    switch (state) {
      case "speaking":
        return { label: "AI is Speaking...", bgOuter: "bg-blue-100 scale-110 shadow-lg shadow-blue-200", bgInner: "bg-blue-500 animate-pulse", textColor: "text-blue-600" };
      case "listening":
        return { label: "Listening to you...", bgOuter: "bg-green-100 scale-100 shadow-md", bgInner: "bg-green-500", textColor: "text-green-600" };
      case "thinking":
        return { label: "Thinking...", bgOuter: "bg-purple-100 scale-105 shadow-md", bgInner: "bg-purple-500 animate-pulse", textColor: "text-purple-600" };
      case "connecting":
        return { label: "Waiting for agent...", bgOuter: "bg-yellow-100 scale-95 animate-pulse", bgInner: "bg-yellow-500", textColor: "text-yellow-600" };
      case "initializing":
        return { label: "Agent initializing...", bgOuter: "bg-orange-100 scale-95 animate-pulse", bgInner: "bg-orange-400", textColor: "text-orange-600" };
      default:
        return { label: `Status: ${state || "unknown"}`, bgOuter: "bg-gray-100 scale-95", bgInner: "bg-gray-400", textColor: "text-gray-600" };
    }
  };

  const { label, bgOuter, bgInner, textColor } = getStateInfo();

  return (
    <div className="flex flex-col items-center">
      <div className={`w-32 h-32 rounded-full flex items-center justify-center transition-all duration-500 ${bgOuter}`}>
        <div className={`w-24 h-24 rounded-full flex items-center justify-center ${bgInner}`}>
          <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
          </svg>
        </div>
      </div>
      <p className={`mt-4 font-medium capitalize ${textColor}`}>
        {label}
      </p>
      <p className="mt-1 text-xs text-gray-400">
        raw: room={roomState} agent={state} audio={audioTrack ? "yes" : "no"}
      </p>
    </div>
  );
}
