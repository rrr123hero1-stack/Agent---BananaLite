// src/utils/socket.js
import { io } from 'socket.io-client';

// ============================================
// SOCKET.IO CONNECTION
// ============================================
const SOCKET_URL = 'http://127.0.0.1:5000';

// Create socket instance
const socket = io(SOCKET_URL, {
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000,
});

// ============================================
// SOCKET EVENT HANDLERS
// ============================================
export const initSocketListeners = (setSocketConnected, setError, setMessages, setGenerationOutput, setIsGenerating, settings) => {
    
    // Connection events
    socket.on('connect', () => {
        console.log('🟢 Connected to server');
        setSocketConnected(true);
        setError(null);
    });

    socket.on('disconnect', () => {
        console.log('🔴 Disconnected from server');
        setSocketConnected(false);
    });

    socket.on('connect_error', (err) => {
        console.error('❌ Connection error:', err);
        setSocketConnected(false);
        setError('Failed to connect to server');
    });

    // Chat response events
    socket.on('chat_response', (data) => {
        console.log('📨 Chat response:', data);
        if (data && data.response) {
            setMessages(prev => [...prev, { 
                role: 'assistant', 
                content: data.response 
            }]);
        }
    });

    // Streaming events
    socket.on('generation_start', (data) => {
        setIsGenerating(true);
        setGenerationOutput('');
        console.log('⏳', data.status);
    });

    socket.on('generation_chunk', (data) => {
        setGenerationOutput(prev => prev + data.text);
    });

    socket.on('generation_complete', (data) => {
        setIsGenerating(false);
        if (data && data.model) {
            console.log(`✅ Generation complete from ${data.model}`);
        }
    });

    socket.on('generation_error', (data) => {
        setIsGenerating(false);
        setError(data.error);
        console.error('❌ Generation error:', data.error);
    });

    return socket;
};

// ============================================
// SOCKET EMIT FUNCTIONS
// ============================================
export const sendChatMessage = (message, temperature, maxTokens, imageBase64) => {
    if (socket.connected) {
        socket.emit('chat_request', {
            prompt: message,
            temperature: temperature || 0.7,
            max_tokens: maxTokens || 2048,
            images: imageBase64 ? [imageBase64] : []
        });
        return true;
    }
    return false;
};

export const sendPing = () => {
    socket.emit('ping');
};

export const disconnectSocket = () => {
    if (socket) {
        socket.disconnect();
    }
};

// ============================================
// EXPORT
// ============================================
export default socket;