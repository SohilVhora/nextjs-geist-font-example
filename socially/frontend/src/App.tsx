import AudioStream from './components/AudioStream'

function App() {
  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Socially</h1>
        <p>Real-time Audio Transcription & Emotion Analysis</p>
      </header>
      <main className="app-main">
        <AudioStream />
      </main>
      <footer className="app-footer">
        <p>Powered by Wav2Vec2 and WebRTC</p>
      </footer>
    </div>
  )
}

export default App
