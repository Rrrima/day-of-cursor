import React, { useRef, useEffect } from "react";

function TimelineControls({
  currentIndex,
  totalFrames,
  currentData,
  isPlaying,
  playbackSpeed,
  isFpsMode,
  isBlinkEnabled,
  onSliderChange,
  onPlayPause,
  onSpeedChange,
  onFpsModeToggle,
  onBlinkToggle,
}) {
  const progressRef = useRef(null);

  useEffect(() => {
    if (progressRef.current) {
      const progress = (currentIndex / (totalFrames - 1)) * 100;
      progressRef.current.style.width = `${progress}%`;
    }
  }, [currentIndex, totalFrames]);

  const handleSliderInput = (e) => {
    const index = parseInt(e.target.value, 10);
    onSliderChange(index);
  };

  const handleSpeedChange = (e) => {
    const speed = parseFloat(e.target.value);
    onSpeedChange(speed);
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp * 1000);
    return date.toLocaleTimeString();
  };

  return (
    <div className="controls">
      <div className="timeline-container">
        <div className="timeline-header">
          <div className="playback-controls">
            <button
              className="play-button"
              onClick={onPlayPause}
              title={isPlaying ? "Pause (Space)" : "Play (Space)"}
            >
              {isPlaying ? (
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <rect
                    x="4"
                    y="3"
                    width="3"
                    height="10"
                    rx="1"
                    fill="currentColor"
                  />
                  <rect
                    x="9"
                    y="3"
                    width="3"
                    height="10"
                    rx="1"
                    fill="currentColor"
                  />
                </svg>
              ) : (
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path
                    d="M5 3.5C5 3.22386 5.22386 3 5.5 3C5.62186 3 5.73986 3.04611 5.83 3.13L12.83 8.63C13.0567 8.81958 13.0567 9.18042 12.83 9.37L5.83 14.87C5.73986 14.9539 5.62186 15 5.5 15C5.22386 15 5 14.7761 5 14.5V3.5Z"
                    fill="currentColor"
                  />
                </svg>
              )}
            </button>
            <div className="speed-control">
              <span className="speed-label">{playbackSpeed.toFixed(1)}x</span>
              <input
                type="range"
                className="speed-slider"
                min="0.1"
                max="3"
                step="0.1"
                value={playbackSpeed}
                onChange={handleSpeedChange}
                title="Playback Speed"
              />
            </div>
          </div>
          <div className="fps-toggle-container">
            <label className="fps-toggle-label">
              <input
                type="checkbox"
                className="fps-checkbox"
                checked={isFpsMode}
                onChange={onFpsModeToggle}
              />
              <span className="fps-toggle-slider"></span>
              <span className="fps-toggle-text">Cursor's POV</span>
            </label>
          </div>
          {isFpsMode && (
            <div className="blink-toggle-container">
              <label className="blink-toggle-label">
                <input
                  type="checkbox"
                  className="blink-checkbox"
                  checked={isBlinkEnabled}
                  onChange={onBlinkToggle}
                />
                <span className="blink-toggle-slider"></span>
                <span className="blink-toggle-text">Blink</span>
              </label>
            </div>
          )}
          <div className="timeline-label">
            <span></span>
            <span id="frameCounter">
              {currentIndex + 1} / {totalFrames}
            </span>
          </div>
        </div>
        <div className="slider-wrapper">
          <div className="slider-track"></div>
          <div ref={progressRef} className="slider-progress"></div>
          <input
            type="range"
            min="0"
            max={totalFrames - 1}
            value={currentIndex}
            step="1"
            onInput={handleSliderInput}
            onChange={handleSliderInput}
          />
        </div>
      </div>

      <div className="info">
        <div className="timestamp">{formatTime(currentData.timestamp)}</div>
        <div className="position">
          x: {Math.round(currentData.x)} | y: {Math.round(currentData.y)}
        </div>
      </div>
    </div>
  );
}

export default TimelineControls;
