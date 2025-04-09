import React, { useEffect, useRef, useState } from 'react';
import { Room, RoomOptions } from 'livekit-client';
import { LIVEKIT_WS_URL } from '../../config';
import { useAuth } from '../../contexts/AuthContext';
import { 
  Box, 
  IconButton, 
  Paper, 
  Typography,
  CircularProgress,
  styled,
  Button
} from '@mui/material';
import MicIcon from '@mui/icons-material/Mic';
import StopIcon from '@mui/icons-material/Stop';
import axios from 'axios';

// Styled components
const LoadingContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  height: '500px',
  width: '100%',
  maxWidth: '600px',
  marginTop: '20px',
  backgroundColor: theme.palette.background.paper,
  borderRadius: '12px',
  boxShadow: theme.shadows[3],
  gap: theme.spacing(2)
}));

const ChatContainer = styled(Paper)(({ theme }) => ({
  display: 'flex',
  flexDirection: 'column',
  height: '450px',
  width: '100%',
  maxWidth: '600px',
  marginTop: '20px',
  backgroundColor: theme.palette.background.paper,
  borderRadius: '12px',
  boxShadow: theme.shadows[3],
  overflow: 'hidden',
}));

const ConversationContainer = styled(Box)(({ theme }) => ({
  flex: 1,
  overflowY: 'auto',
  padding: theme.spacing(2),
  display: 'flex',
  flexDirection: 'column',
  gap: theme.spacing(2),
  '&::-webkit-scrollbar': {
    width: '8px',
  },
  '&::-webkit-scrollbar-track': {
    background: theme.palette.background.paper,
  },
  '&::-webkit-scrollbar-thumb': {
    backgroundColor: theme.palette.primary.light,
    borderRadius: '4px',
  }
}));

const MessageBubble = styled(Box, {
  shouldForwardProp: (prop) => prop !== 'isUser'
})<{ isUser: boolean }>(({ theme, isUser }) => ({
  maxWidth: '80%',
  padding: theme.spacing(1.5),
  borderRadius: '12px',
  alignSelf: isUser ? 'flex-end' : 'flex-start',
  backgroundColor: isUser ? theme.palette.primary.main : theme.palette.grey[100],
  color: isUser ? theme.palette.primary.contrastText : theme.palette.text.primary,
  position: 'relative',
  '&::after': {
    content: '""',
    position: 'absolute',
    bottom: '8px',
    [isUser ? 'right' : 'left']: '-8px',
    width: '0',
    height: '0',
    borderStyle: 'solid',
    borderWidth: isUser ? '8px 0 8px 8px' : '8px 8px 8px 0',
    borderColor: isUser 
      ? `transparent transparent transparent ${theme.palette.primary.main}`
      : `transparent ${theme.palette.grey[100]} transparent transparent`,
  }
}));

const ControlsContainer = styled(Box)(({ theme }) => ({
  padding: theme.spacing(2),
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  backgroundColor: theme.palette.background.default,
  borderTop: `1px solid ${theme.palette.divider}`
}));

const RecordButton = styled(IconButton, {
  shouldForwardProp: (prop) => prop !== 'isRecording' && prop !== 'audioLevel'
})<{ isRecording?: boolean; audioLevel?: number }>(({ theme, isRecording, audioLevel = 0 }) => ({
  width: '64px',
  height: '64px',
  backgroundColor: isRecording ? theme.palette.error.main : theme.palette.primary.main,
  color: theme.palette.common.white,
  transition: 'all 0.3s ease',
  position: 'relative',
  '&:hover': {
    backgroundColor: isRecording ? theme.palette.error.dark : theme.palette.primary.dark,
  },
  '&::after': {
    content: '""',
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    width: `${100 + (audioLevel * 100)}%`,
    height: `${100 + (audioLevel * 100)}%`,
    borderRadius: '50%',
    border: `2px solid ${isRecording ? theme.palette.error.main : theme.palette.primary.main}`,
    opacity: 0.5,
    animation: isRecording ? 'ripple 1.5s infinite' : 'none'
  },
  '@keyframes ripple': {
    '0%': {
      transform: 'translate(-50%, -50%) scale(1)',
      opacity: 0.5,
    },
    '100%': {
      transform: 'translate(-50%, -50%) scale(1.5)',
      opacity: 0,
    }
  }
}));

interface Property {
  id: string;
  name: string;
  location: string;
  property_type: string;
  price: number;
  bedrooms: number;
  area: number;
  description: string;
  images: string[];
}

interface VoiceChatProps {
  sessionId: string;
  onMessage: (message: string) => Promise<void>;
  onToggleInterface: (show: boolean) => void;
  showInterface: boolean;
  onPropertiesUpdate?: (properties: Property[]) => void;
}

export const VoiceChat: React.FC<VoiceChatProps> = ({ 
  sessionId, 
  onMessage, 
  onToggleInterface, 
  showInterface, 
  onPropertiesUpdate 
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  const [initError, setInitError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [audioLevel, setAudioLevel] = useState(0);
  const [conversation, setConversation] = useState<Array<{ role: 'ai' | 'user', message: string }>>([
    { role: 'ai', message: "Hi, I'm Janaki! How can I help you find your perfect property?" }
  ]);
  const { user } = useAuth();
  const [room, setRoom] = useState<Room | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const conversationEndRef = useRef<HTMLDivElement>(null);

  const initRoom = async () => {
    if (!user?.id) {
      setIsInitializing(false);
      setInitError('User not authenticated');
      return;
    }
    
    try {
      setIsInitializing(true);
      setInitError(null);

      // Get LiveKit token
      const response = await axios.post('/api/voice/conversation/room', {
        user_id: user.id
      });
      
      console.log('LiveKit response:', response.data);
      
      if (!response.data.token || !response.data.livekit_ws_url) {
        throw new Error(`Invalid response from server. Expected token and livekit_ws_url, got: ${JSON.stringify(response.data)}`);
      }
      
      const { token, room: roomName, livekit_ws_url } = response.data;
      
      console.log('Using WebSocket URL:', livekit_ws_url);
      
      // Connect to LiveKit room
      const roomOptions: RoomOptions = {
        adaptiveStream: true,
        dynacast: true,
        publishDefaults: {
          simulcast: false,
          videoSimulcastLayers: [],
        },
      };

      const newRoom = new Room(roomOptions);
      await newRoom.connect(livekit_ws_url, token);
      setRoom(newRoom);
      setIsInitializing(false);
      
    } catch (error) {
      console.error('Failed to initialize LiveKit room:', error);
      setInitError('Failed to initialize chat room');
      setIsInitializing(false);
    }
  };

  useEffect(() => {
    initRoom();
    return () => {
      room?.disconnect();
    };
  }, [user?.id]);

  useEffect(() => {
    if (!user?.token) return;

    const initWebSocket = () => {
      const ws = new WebSocket(`ws://localhost:8000/api/voice/conversation/voice?token=${encodeURIComponent(user.token)}`);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
      };

      ws.onmessage = async (event) => {
        const data = event.data;
        if (data instanceof Blob) {
          try {
            // Ensure we have valid audio data
            if (data.size > 0) {
              // Create a new blob with explicit audio/mpeg type
              const audioBlob = new Blob([data], { type: 'audio/mpeg' });
              console.log('Created audio blob:', {
                size: audioBlob.size,
                type: audioBlob.type
              });

              // Create an object URL for the blob
              const audioUrl = URL.createObjectURL(audioBlob);
              console.log('Created audio URL:', audioUrl);
              
              // Create and set up the audio element
              const audio = new Audio();
              
              // Set up promise-based play handler
              const playAudio = async () => {
                try {
                  await audio.play();
                  console.log('Audio playback started successfully');
                } catch (error) {
                  console.error('Audio play failed:', error);
                  // Try fallback approach if initial play fails
                  setTimeout(async () => {
                    try {
                      await audio.play();
                      console.log('Audio playback started after retry');
                    } catch (retryError) {
                      console.error('Audio play retry failed:', retryError);
                    }
                  }, 100);
                }
              };

              // Set up event handlers
              audio.oncanplay = () => {
                console.log('Audio can play, starting playback...');
                playAudio();
              };
              
              audio.onended = () => {
                console.log('Audio playback completed');
                URL.revokeObjectURL(audioUrl);
              };
              
              audio.onerror = (e) => {
                console.error('Audio error:', {
                  error: e,
                  code: audio.error?.code,
                  message: audio.error?.message
                });
                URL.revokeObjectURL(audioUrl);
              };

              // Load the audio
              audio.src = audioUrl;
              audio.load(); // Explicitly load the audio
            } else {
              console.error('Received empty audio blob');
            }
          } catch (error) {
            console.error('Error playing audio:', error);
          }
        } else {
          // Handle JSON messages
          try {
            const jsonData = JSON.parse(data);
            console.log('Received message:', jsonData);
            switch (jsonData.type) {
              case 'error':
                console.error('Server error:', jsonData.message);
                setError(jsonData.message);
                setIsProcessing(false);
                break;
              case 'connection':
                console.log('Connected:', jsonData.message);
                break;
              case 'transcription':
                setConversation(prev => [...prev, { role: 'user', message: jsonData.text }]);
                break;
              case 'response':
                setConversation(prev => [...prev, { role: 'ai', message: jsonData.text }]);
                // Handle properties if they exist
                if (jsonData.properties && Array.isArray(jsonData.properties) && onPropertiesUpdate) {
                  console.log('Updating properties:', jsonData.properties);
                  onPropertiesUpdate(jsonData.properties);
                }
                setIsProcessing(false);
                break;

            }
          } catch (error) {
            console.error('Error parsing JSON message:', error);
          }
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsProcessing(false);
      };

      ws.onclose = () => {
        console.log('WebSocket closed');
        setIsProcessing(false);
        // Attempt to reconnect after a delay
        setTimeout(initWebSocket, 3000);
      };
    };

    initWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [user?.token]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // Set up audio analyzer
      const audioContext = new AudioContext();
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;

      // Start level monitoring
      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      const updateLevel = () => {
        if (!isRecording) return;
        analyser.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
        setAudioLevel(average);
        requestAnimationFrame(updateLevel);
      };
      updateLevel();

      // Set up media recorder with specific MIME type
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });
        chunksRef.current = [];
        setIsProcessing(true);

        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(audioBlob);
        }
      };

      mediaRecorder.start(1000);
      setIsRecording(true);
    } catch (error) {
      console.error('Error starting recording:', error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      streamRef.current?.getTracks().forEach(track => track.stop());
      setIsRecording(false);
      setAudioLevel(0);
    }
  };

  useEffect(() => {
    if (conversationEndRef.current) {
      conversationEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [conversation]);

  if (isInitializing) {
    return (
      <LoadingContainer>
        <CircularProgress />
        <Typography variant="body1" color="textSecondary">
          Initializing chat interface...
        </Typography>
      </LoadingContainer>
    );
  }

  if (initError) {
    return (
      <LoadingContainer>
        <Typography variant="body1" color="error">
          {initError}
        </Typography>
        <Button
          variant="contained"
          color="primary"
          onClick={() => {
            setInitError(null);
            setIsInitializing(true);
            initRoom();
          }}
        >
          Retry
        </Button>
      </LoadingContainer>
    );
  }

  return (
    <ChatContainer >
      <ConversationContainer>
        {conversation.map((msg, index) => (
          <MessageBubble key={index} isUser={msg.role === 'user'}>
            <Typography variant="body1">
              {msg.message}
            </Typography>
          </MessageBubble>
        ))}
        <div ref={conversationEndRef} />
      </ConversationContainer>
      <ControlsContainer>
        <RecordButton
          isRecording={isRecording}
          audioLevel={audioLevel / 128}
          onClick={isRecording ? stopRecording : startRecording}
          disabled={isProcessing}
          size="large"
        >
          {isProcessing ? (
            <CircularProgress size={24} color="inherit" />
          ) : isRecording ? (
            <StopIcon fontSize="large" />
          ) : (
            <MicIcon fontSize="large" />
          )}
        </RecordButton>
      </ControlsContainer>
    </ChatContainer>
  );
};

export default VoiceChat;
