import React, { useState, useEffect, useRef, useCallback } from "react";
import ScreenshotDisplay from "./ScreenshotDisplay";
import TimelineControls from "./TimelineControls";

function TimelineViewer({ timelineData }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1); // 1x speed
  const [isFpsMode, setIsFpsMode] = useState(false); // FPS mode toggle
  const [isBlinkEnabled, setIsBlinkEnabled] = useState(true); // Blink effect toggle
  const playIntervalRef = useRef(null);

  // Auto-play functionality
  useEffect(() => {
    if (isPlaying) {
      const interval = 100 / playbackSpeed; // Adjust interval based on speed
      playIntervalRef.current = setInterval(() => {
        setCurrentIndex((prevIndex) => {
          if (prevIndex >= timelineData.length - 1) {
            setIsPlaying(false); // Stop at the end
            return prevIndex;
          }
          return prevIndex + 1;
        });
      }, interval);

      return () => {
        if (playIntervalRef.current) {
          clearInterval(playIntervalRef.current);
        }
      };
    } else {
      if (playIntervalRef.current) {
        clearInterval(playIntervalRef.current);
      }
    }
  }, [isPlaying, playbackSpeed, timelineData.length]);

  // Keyboard controls
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "ArrowLeft" && currentIndex > 0) {
        setCurrentIndex(currentIndex - 1);
        setIsPlaying(false); // Pause when manually navigating
      } else if (
        e.key === "ArrowRight" &&
        currentIndex < timelineData.length - 1
      ) {
        setCurrentIndex(currentIndex + 1);
        setIsPlaying(false); // Pause when manually navigating
      } else if (e.key === " ") {
        // Spacebar to play/pause
        e.preventDefault();
        setIsPlaying(!isPlaying);
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [currentIndex, timelineData.length, isPlaying]);

  // Preload images around current position
  useEffect(() => {
    const preloadImages = () => {
      timelineData.forEach((data, index) => {
        if (Math.abs(index - currentIndex) < 5) {
          const img = new Image();
          img.src = data.screenshot;
        }
      });
    };

    const timer = setTimeout(preloadImages, 100);
    return () => clearTimeout(timer);
  }, [currentIndex, timelineData]);

  const handleSliderChange = useCallback((newIndex) => {
    setCurrentIndex(newIndex);
    setIsPlaying(false); // Pause when manually scrubbing
  }, []);

  const handlePlayPause = useCallback(() => {
    if (currentIndex >= timelineData.length - 1) {
      // If at the end, restart from beginning
      setCurrentIndex(0);
      setIsPlaying(true);
    } else {
      setIsPlaying(!isPlaying);
    }
  }, [isPlaying, currentIndex, timelineData.length]);

  const currentData = timelineData[currentIndex];

  if (!currentData) return null;

  return (
    <div className="container">
      <ScreenshotDisplay
        data={currentData}
        onImageLoad={() => setImageLoaded(true)}
        isFpsMode={isFpsMode}
        isBlinkEnabled={isBlinkEnabled}
      />
      <TimelineControls
        currentIndex={currentIndex}
        totalFrames={timelineData.length}
        currentData={currentData}
        isPlaying={isPlaying}
        playbackSpeed={playbackSpeed}
        isFpsMode={isFpsMode}
        isBlinkEnabled={isBlinkEnabled}
        onSliderChange={handleSliderChange}
        onPlayPause={handlePlayPause}
        onSpeedChange={setPlaybackSpeed}
        onFpsModeToggle={() => setIsFpsMode(!isFpsMode)}
        onBlinkToggle={() => setIsBlinkEnabled(!isBlinkEnabled)}
      />
    </div>
  );
}

export default TimelineViewer;
