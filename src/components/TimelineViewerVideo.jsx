import React, { useState, useRef, useEffect, useCallback } from "react";
import ScreenshotDisplayVideo from "./ScreenshotDisplayVideo";
import TimelineControls from "./TimelineControls";

function TimelineViewerVideo({ timelineData, videoSrc }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [isFpsMode, setIsFpsMode] = useState(false);
  const [isBlinkEnabled, setIsBlinkEnabled] = useState(true);
  const [videoLoaded, setVideoLoaded] = useState(false);

  const videoRef = useRef(null);
  const playIntervalRef = useRef(null);
  const playingIndexRef = useRef(currentIndex);

  const currentData = timelineData[currentIndex];

  // Keep playingIndexRef in sync with currentIndex
  useEffect(() => {
    playingIndexRef.current = currentIndex;
  }, [currentIndex]);

  // Initialize video when component mounts
  useEffect(() => {
    if (videoRef.current && videoSrc) {
      videoRef.current.src = videoSrc;
    }
  }, [videoSrc]);

  // Playback control with real-time timing
  useEffect(() => {
    if (isPlaying) {
      const advanceFrame = () => {
        const index = playingIndexRef.current;

        if (index >= timelineData.length - 1) {
          setIsPlaying(false);
          return;
        }

        const nextIndex = index + 1;

        // Calculate actual time difference between frames
        const currentFrame = timelineData[index];
        const nextFrame = timelineData[nextIndex];
        const timeDiff = (nextFrame.timestamp - currentFrame.timestamp) * 1000; // Convert to ms

        // Schedule next frame based on actual time difference and playback speed
        const adjustedInterval = timeDiff / playbackSpeed;

        playIntervalRef.current = setTimeout(() => {
          setCurrentIndex(nextIndex);
          playingIndexRef.current = nextIndex;
          advanceFrame();
        }, adjustedInterval);
      };

      // Start playback from current position
      advanceFrame();

      return () => {
        if (playIntervalRef.current) {
          clearTimeout(playIntervalRef.current);
          playIntervalRef.current = null;
        }
      };
    } else {
      if (playIntervalRef.current) {
        clearTimeout(playIntervalRef.current);
        playIntervalRef.current = null;
      }
    }
  }, [isPlaying, playbackSpeed, timelineData]);

  // Keyboard controls
  useEffect(() => {
    const handleKeyPress = (e) => {
      if (e.key === " " || e.key === "Spacebar") {
        e.preventDefault();
        setIsPlaying((prev) => !prev);
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        setCurrentIndex((prev) => Math.min(prev + 1, timelineData.length - 1));
      } else if (e.key === "ArrowLeft") {
        e.preventDefault();
        setCurrentIndex((prev) => Math.max(prev - 1, 0));
      }
    };

    window.addEventListener("keydown", handleKeyPress);
    return () => window.removeEventListener("keydown", handleKeyPress);
  }, [timelineData.length]);

  const handleSliderChange = useCallback((index) => {
    setCurrentIndex(index);
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

  const handleVideoLoad = useCallback(() => {
    setVideoLoaded(true);
  }, []);

  if (!currentData) {
    return <div>No data available</div>;
  }

  return (
    <div className="container">
      {!videoLoaded && (
        <div className="loading-video">
          <div className="spinner"></div>
          <div>Loading video...</div>
        </div>
      )}
      <ScreenshotDisplayVideo
        data={currentData}
        videoRef={videoRef}
        onVideoLoad={handleVideoLoad}
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

export default TimelineViewerVideo;
