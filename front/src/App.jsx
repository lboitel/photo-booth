import { useRef, useState, useEffect } from 'react';
import cameraButton from './imgs/camera_button.png';
import pineappleBunPhoto from './imgs/pineapple_bun_photo.png';
import pineappleBunSmile from './imgs/pineapple_bun_smile.png';
import pineappleBunStars from './imgs/pineapple_bun_stars.png';

const bunSources = [pineappleBunPhoto, pineappleBunSmile, pineappleBunStars];

export default function App() {
  const frameRef = useRef(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [drops, setDrops] = useState([]);
  const [nextId, setNextId] = useState(0);
  const [showWebcam, setShowWebcam] = useState(false);
  const [countdown, setCountdown] = useState(null);
  const [photoTaken, setPhotoTaken] = useState(null);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (showWebcam && videoRef.current) {
      navigator.mediaDevices.getUserMedia({ video: true })
        .then((stream) => {
          videoRef.current.srcObject = stream;
        })
        .catch((error) => {
          console.error('Error accessing webcam:', error);
        });
    }
  }, [showWebcam]);

  const handleClick = () => {
    const frameWidth = frameRef.current?.clientWidth ?? 540;
    const numBuns = 12;
    const newDrops = Array.from({ length: numBuns }, (_, index) => {
      const id = `${Date.now()}-${nextId + index}`;
      return {
        id,
        x: (frameWidth - 104) * (index / (numBuns - 1)),
        img: bunSources[Math.floor(Math.random() * bunSources.length)],
        delay: Math.random() * 0.2,
        rotation: Math.random() * 360,
        scale: 0.8 + Math.random() * 0.2,
      };
    });

    setNextId((current) => current + 8);
    setDrops((current) => [...current, ...newDrops]);

    // Show webcam after animation
    setTimeout(() => {
      setShowWebcam(true);
    }, 2500);
  };

  const handleDropEnd = (id) => {
    setDrops((current) => current.filter((drop) => drop.id !== id));
  };

  const handleTakePhoto = () => {
    if (countdown !== null) return;

    let count = 5;
    setCountdown(count);

    const countdownInterval = setInterval(() => {
      count--;
      if (count > 0) {
        setCountdown(count);
      } else {
        clearInterval(countdownInterval);
        setCountdown(null);
        takePhoto();
      }
    }, 1000);
  };

  const takePhoto = () => {
    const canvas = canvasRef.current;
    const video = videoRef.current;
    const context = canvas.getContext('2d');

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    const photoDataUrl = canvas.toDataURL('image/png');
    setPhotoTaken(photoDataUrl);
    setIsSaving(true);

    // Simulate loading screen for 5 seconds, then return to home
    setTimeout(() => {
      setIsSaving(false);
      setPhotoTaken(null);
      setShowWebcam(false);
      setDrops([]);
    }, 5000);

    // Send photo to server asynchronously without blocking user flow
    fetch('http://localhost:3001/api/save-photo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ photo: photoDataUrl })
    })
      .then((res) => res.json())
      .then((data) => {
        console.log('Photo saved:', data);
      })
      .catch((error) => {
        console.error('Error saving photo:', error);
      });
  };

  return (
    <div className="app-shell">
      <div className="frame" ref={frameRef} onClick={showWebcam && !photoTaken && countdown === null ? handleTakePhoto : undefined}>
        <div className="spotlight" />
        <div className="frame-glow" />
        {drops.map((drop) => (
          <img
            key={drop.id}
            src={drop.img}
            alt="Pineapple bun"
            className="rain-drop"
            style={{
              left: `${drop.x}px`,
              animationDelay: `${drop.delay}s`,
              '--drop-rotation': `${drop.rotation}deg`,
              '--drop-scale': `${drop.scale}`,
            }}
            onAnimationEnd={() => handleDropEnd(drop.id)}
          />
        ))}
        {!showWebcam && (
          <>
            <button type="button" className="camera-button" onClick={handleClick}>
              <img src={cameraButton} alt="Camera button" />
            </button>
            <div className="camera-label">Memories take-away</div>
          </>
        )}
        {showWebcam && !photoTaken && (
          <>
            <video ref={videoRef} autoPlay playsInline muted className="webcam-video" />
            {countdown === null && <div className="press-me-text">✨ Press me ✨</div>}
            {countdown !== null && (
              <div className="countdown">
                <span className="countdown-number">{countdown}</span>
              </div>
            )}
          </>
        )}
        {photoTaken && !isSaving && (
          <img src={photoTaken} alt="Captured photo" className="captured-photo" />
        )}
        {isSaving && (
          <div className="loading-overlay">
            <img src={pineappleBunPhoto} alt="Pineapple bun" className="loading-bun" />
            <div className="loading-text">Gau Dim! Just a few seconds</div>
          </div>
        )}
      </div>
      <canvas ref={canvasRef} style={{ display: 'none' }} />
    </div>
  );
}
