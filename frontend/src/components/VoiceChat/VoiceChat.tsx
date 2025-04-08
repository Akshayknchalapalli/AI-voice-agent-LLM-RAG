import React, { useRef, useState, useEffect } from 'react';
import { Box, IconButton, Typography, Paper, CircularProgress } from '@mui/material';
import { Mic, Stop } from '@mui/icons-material';
import { toast } from 'react-toastify';

const VoiceChat: React.FC = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(true);
  const [audioLevel, setAudioLevel] = useState(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number>();

  const connectWebSocket = () => {
    const token = localStorage.getItem('token');
    if (!token) {
      toast.error('Authentication required');
      setIsConnecting(false);
      return null;
    }

    try {
      const ws = new WebSocket(`ws://${window.location.hostname}:8000/api/voice/conversation/voice`);
      ws.binaryType = 'arraybuffer';

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setIsConnecting(false);
        ws.send(JSON.stringify({
          type: 'auth',
          token: token
        }));
      };

      ws.onmessage = async (event) => {
        try {
          // Handle binary audio data
          if (event.data instanceof ArrayBuffer) {
            const audioBlob = new Blob([event.data], { type: 'audio/webm;codecs=opus' });
            const audioUrl = URL.createObjectURL(audioBlob);
            const audio = new Audio(audioUrl);
            await audio.play();
            setIsProcessing(false);
            return;
          }

          // Handle text messages
          const data = JSON.parse(event.data);
          
          switch (data.type) {
            case 'connection':
              toast.success(data.message);
              break;
              
            case 'transcript':
              setIsProcessing(true);
              toast.info(`You: ${data.text}`, {
                position: "top-right",
                autoClose: 3000
              });
              break;
              
            case 'response':
              toast.success(`AI: ${data.text}`, {
                position: "top-left",
                autoClose: 5000
              });
              break;
              
            case 'error':
              setIsProcessing(false);
              toast.error(data.message);
              break;
          }
        } catch (error) {
          console.error('Error handling WebSocket message:', error);
          setIsProcessing(false);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
        setIsProcessing(false);
        setIsRecording(false);
        setIsConnecting(false);
        toast.error('Connection error');
      };

      ws.onclose = () => {
        console.log('WebSocket connection closed');
        setIsConnected(false);
        setIsProcessing(false);
        setIsRecording(false);
        setIsConnecting(false);
      };

      return ws;
    } catch (error) {
      console.error('Error creating WebSocket:', error);
      setIsConnecting(false);
      toast.error('Failed to connect');
      return null;
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          sampleSize: 16,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });
      streamRef.current = stream;

      // Set up audio analyzer
      const audioContext = new AudioContext();
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;

      // Start audio level monitoring
      const updateAudioLevel = () => {
        if (analyserRef.current) {
          const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
          analyserRef.current.getByteFrequencyData(dataArray);
          const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
          setAudioLevel(average);
        }
        animationFrameRef.current = requestAnimationFrame(updateAudioLevel);
      };
      updateAudioLevel();

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus',
        audioBitsPerSecond: 16000
      });
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        if (chunksRef.current.length > 0 && wsRef.current?.readyState === WebSocket.OPEN) {
          const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm;codecs=opus' });
          chunksRef.current = [];
          
          // Send the complete audio data
          const arrayBuffer = await audioBlob.arrayBuffer();
          wsRef.current.send(arrayBuffer);
        }
      };

      mediaRecorder.start(1000); // Collect data every second
      setIsRecording(true);
    } catch (error) {
      console.error('Error starting recording:', error);
      toast.error('Failed to start recording');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && streamRef.current) {
      mediaRecorderRef.current.stop();
      streamRef.current.getTracks().forEach(track => track.stop());
      setIsRecording(false);
      setAudioLevel(0);
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    }
  };

  useEffect(() => {
    const ws = connectWebSocket();
    if (ws) {
      wsRef.current = ws;
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  return (
    <Box
      sx={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 3,
      }}
    >
      <Paper
        elevation={3}
        sx={{
          padding: 4,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 2,
          borderRadius: 3,
          backgroundColor: 'background.paper',
        }}
      >
        <Typography variant="h6" color="text.primary" textAlign="center">
          {isConnecting ? 'Connecting to voice service...' :
           isRecording ? 'Listening...' : 
           'Click the microphone to start speaking'}
        </Typography>

        <Box
          sx={{
            position: 'relative',
            width: 80,
            height: 80,
          }}
        >
          {isConnecting ? (
            <CircularProgress size={56} />
          ) : (
            <>
              {/* Sound wave visualization */}
              {isRecording && (
                <Box
                  sx={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    width: `${100 + audioLevel}px`,
                    height: `${100 + audioLevel}px`,
                    borderRadius: '50%',
                    border: '2px solid',
                    borderColor: 'primary.main',
                    opacity: 0.5,
                    transition: 'all 0.1s ease-in-out',
                  }}
                />
              )}
              
              <IconButton
                color={isRecording ? 'error' : 'primary'}
                onClick={isRecording ? stopRecording : startRecording}
                disabled={!isConnected || isProcessing}
                sx={{
                  width: '100%',
                  height: '100%',
                  '&.Mui-disabled': {
                    opacity: 0.5,
                  },
                }}
              >
                {isRecording ? <Stop /> : <Mic />}
              </IconButton>
            </>
          )}
        </Box>

        {isProcessing && (
          <Typography variant="body2" color="text.secondary">
            Processing...
          </Typography>
        )}
      </Paper>
    </Box>
  );
};

export default VoiceChat;
