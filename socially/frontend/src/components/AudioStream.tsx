import React, { useState, useEffect, useRef, useCallback } from 'react'

interface AudioResult {
  transcription?: string
  emotion?: string
  timestamp?: number
  error?: string
}

const AudioStream: React.FC = () => {
  const [isRecording, setIsRecording] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [transcription, setTranscription] = useState('')
  const [emotion, setEmotion] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [status, setStatus] = useState('Ready to start')
  
  const wsRef = useRef<WebSocket | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const streamRef = useRef<MediaStream | null>(null)

  const connectWebSocket = useCallback(() => {
    try {
      const ws = new WebSocket('ws://localhost:8000/ws')
      
      ws.onopen = () => {
        console.log('WebSocket connected')
        setIsConnected(true)
        setError(null)
        setStatus('Connected to server')
      }
      
      ws.onmessage = (event) => {
        try {
          const data: AudioResult = JSON.parse(event.data)
          console.log('Received data:', data)
          
          if (data.error) {
            setError(data.error)
            setStatus('Error occurred')
          } else {
            setTranscription(data.transcription || '')
            setEmotion(data.emotion || '')
            setStatus('Processing complete')
          }
        } catch (e) {
          console.error('Error parsing server message:', e)
          setError('Error parsing server response')
        }
      }
      
      ws.onerror = (e) => {
        console.error('WebSocket error:', e)
        setError('WebSocket connection error')
        setIsConnected(false)
        setStatus('Connection error')
      }
      
      ws.onclose = () => {
        console.log('WebSocket closed')
        setIsConnected(false)
        setStatus('Disconnected from server')
      }
      
      wsRef.current = ws
    } catch (e) {
      setError('Failed to connect to server')
      setStatus('Connection failed')
    }
  }, [])

  useEffect(() => {
    connectWebSocket()
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
      }
    }
  }, [connectWebSocket])

  const startRecording = async () => {
    try {
      setError(null)
      setStatus('Requesting microphone access...')
      
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      })
      
      streamRef.current = stream
      
      // Create MediaRecorder with appropriate settings
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      })
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0 && wsRef.current?.readyState === WebSocket.OPEN) {
          // Convert blob to array buffer and send
          event.data.arrayBuffer().then((buffer) => {
            if (wsRef.current?.readyState === WebSocket.OPEN) {
              wsRef.current.send(buffer)
            }
          }).catch(err => {
            console.error('Error converting audio data:', err)
          })
        }
      }
      
      mediaRecorder.onerror = (event) => {
        console.error('MediaRecorder error:', event)
        setError('Recording error occurred')
        setStatus('Recording error')
      }
      
      mediaRecorder.onstart = () => {
        setStatus('Recording... Speak now!')
      }
      
      mediaRecorder.onstop = () => {
        setStatus('Recording stopped')
      }
      
      // Start recording with small time slices for real-time streaming
      mediaRecorder.start(250) // Send data every 250ms
      mediaRecorderRef.current = mediaRecorder
      setIsRecording(true)
      
    } catch (e) {
      console.error('Error starting recording:', e)
      setError('Microphone access denied or not available')
      setStatus('Microphone access failed')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
    }
    
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
    }
    
    setIsRecording(false)
    setStatus('Recording stopped')
  }

  const reconnect = () => {
    if (wsRef.current) {
      wsRef.current.close()
    }
    connectWebSocket()
  }

  return (
    <div className="audio-stream-container">
      <div className="status-section">
        <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
          <div className="status-indicator"></div>
          <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
        </div>
        <div className="current-status">{status}</div>
      </div>

      <div className="controls-section">
        {!isRecording ? (
          <button 
            className="record-button start" 
            onClick={startRecording}
            disabled={!isConnected}
          >
            Start Recording
          </button>
        ) : (
          <button 
            className="record-button stop" 
            onClick={stopRecording}
          >
            Stop Recording
          </button>
        )}
        
        {!isConnected && (
          <button className="reconnect-button" onClick={reconnect}>
            Reconnect
          </button>
        )}
      </div>

      {error && (
        <div className="error-section">
          <div className="error-message">{error}</div>
        </div>
      )}

      <div className="results-section">
        <div className="result-card">
          <h3>Transcription</h3>
          <div className="result-content transcription">
            {transcription || 'No transcription yet...'}
          </div>
        </div>
        
        <div className="result-card">
          <h3>Emotion</h3>
          <div className="result-content emotion">
            <span className={`emotion-badge ${emotion.toLowerCase()}`}>
              {emotion || 'No emotion detected...'}
            </span>
          </div>
        </div>
      </div>

      <div className="instructions">
        <h4>Instructions:</h4>
        <ul>
          <li>Click "Start Recording" to begin audio capture</li>
          <li>Speak clearly into your microphone</li>
          <li>The system will automatically detect when you stop speaking</li>
          <li>Transcription and emotion analysis will appear below</li>
        </ul>
      </div>
    </div>
  )
}

export default AudioStream
