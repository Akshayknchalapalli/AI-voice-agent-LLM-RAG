import React, { useState } from 'react';
import { Fab, Dialog, IconButton, Typography, Box } from '@mui/material';
import MicIcon from '@mui/icons-material/Mic';
import CloseIcon from '@mui/icons-material/Close';
import VoiceChat from '../VoiceChat/VoiceChat';
import styles from './FloatingVoiceChat.module.css';

interface FloatingVoiceChatProps {
  onPropertiesUpdate: (properties: any[]) => void;
}

const FloatingVoiceChat: React.FC<FloatingVoiceChatProps> = ({ onPropertiesUpdate }) => {
  const [isOpen, setIsOpen] = useState(false);

  const handleOpen = () => setIsOpen(true);
  const handleClose = () => setIsOpen(false);

  return (
    <>
      <Fab 
        color="primary" 
        className={styles.floatingButton}
        onClick={handleOpen}
        aria-label="voice chat"
      >
        <MicIcon />
      </Fab>

      <Dialog
        open={isOpen}
        onClose={handleClose}
        maxWidth="sm"
        fullWidth
        classes={{
          paper: styles.dialogPaper
        }}
      >
        <Box className={styles.dialogHeader}>
          <Typography variant="h6">Chat with Janaki</Typography>
          <IconButton onClick={handleClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
        
        <Box className={styles.dialogContent} sx={{padding:"16px" ,overflowY:"hidden" , mt:1}}>
          <VoiceChat 
            sessionId="floating-chat"
            onMessage={async () => {}}
            onToggleInterface={() => {}}
            showInterface={true}
            onPropertiesUpdate={onPropertiesUpdate} 
          />
        </Box>
      </Dialog>
    </>
  );
};

export default FloatingVoiceChat;
