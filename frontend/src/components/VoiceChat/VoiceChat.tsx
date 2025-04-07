import React, { useEffect, useRef, useState } from 'react';
import { Box, Paper, Typography, IconButton } from '@mui/material';
import { Mic, MicOff, Send } from '@mui/icons-material';
import { Room, LocalParticipant, RemoteParticipant } from 'livekit-client';

interface VoiceChatProps {
  sessionId: string;
  onMessage: (message: string) => void;
}

const VoiceChat: React.FC<VoiceChatProps> = ({ sessionId, onMessage }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    // Connect to WebSocket for real-time transcription
    wsRef.current = new WebSocket(`ws://localhost:8000/conversation/voice/${sessionId}`);
    
    wsRef.current.onmessage = (event) => {
      const response = JSON.parse(event.data);
      if (response.type === 'transcript') {
        setTranscript(response.text);
      } else if (response.type === 'response') {
        onMessage(response.text);
        // Play audio response if provided
        if (response.audio) {
          const audio = new Audio(URL.createObjectURL(
            new Blob([response.audio], { type: 'audio/wav' })
          ));
          audio.play();
        }
      }
    };

    return () => {
      wsRef.current?.close();
    };
  }, [sessionId]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
          // Send audio chunk to server
          wsRef.current?.send(event.data);
        }
      };

      mediaRecorderRef.current.onstop = () => {
        audioChunksRef.current = [];
      };

      mediaRecorderRef.current.start(250); // Collect data every 250ms
      setIsRecording(true);
    } catch (error) {
      console.error('Error accessing microphone:', error);
    }
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
  };

  return (
    <Paper elevation={3} sx={{ p: 2, m: 2 }}>
      <Box display="flex" flexDirection="column" gap={2}>
        <Typography variant="h6">Voice Chat</Typography>
        
        <Box sx={{ minHeight: 100, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
          <Typography>{transcript || 'Speak to start...'}</Typography>
        </Box>

        <Box display="flex" justifyContent="center">
          <IconButton
            color={isRecording ? 'error' : 'primary'}
            onClick={isRecording ? stopRecording : startRecording}
            size="large"
          >
            {isRecording ? <MicOff /> : <Mic />}
          </IconButton>
        </Box>
      </Box>
    </Paper>
  );
};

export default VoiceChat;
