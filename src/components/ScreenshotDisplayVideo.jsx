import React, { useRef, useEffect, useCallback, useState } from "react";

function ScreenshotDisplayVideo({
  data,
  videoRef,
  onVideoLoad,
  isFpsMode,
  isBlinkEnabled,
}) {
  const cursorRef = useRef(null);
  const wrapperRef = useRef(null);
  const [isSeeking, setIsSeeking] = useState(false);
  const [pendingData, setPendingData] = useState(null);

  const updateDisplay = useCallback(() => {
    if (!cursorRef.current || !videoRef.current || !wrapperRef.current) return;

    // Get the natural (original) size of the video
    const naturalWidth = videoRef.current.videoWidth;
    const naturalHeight = videoRef.current.videoHeight;

    // Get the displayed size of the video
    const displayedWidth = videoRef.current.clientWidth;
    const displayedHeight = videoRef.current.clientHeight;

    if (naturalWidth === 0 || naturalHeight === 0) return;

    // Calculate scale factors
    const scaleX = displayedWidth / naturalWidth;
    const scaleY = displayedHeight / naturalHeight;

    // Coordinates are stored at original size but video is downsampled to 50%
    // So we need to divide by 2 first, then scale to the displayed size
    const cursorX = (data.x / 2) * scaleX;
    const cursorY = (data.y / 2) * scaleY;

    if (isFpsMode) {
      // FPS Mode: Cursor stays centered, video moves
      const containerRect = wrapperRef.current.getBoundingClientRect();
      const centerX = containerRect.width / 2;
      const centerY = containerRect.height / 2;

      // Calculate offset to move video so cursor position appears at center
      const offsetX = centerX - cursorX;
      const offsetY = centerY - cursorY;

      // Apply transform to video
      videoRef.current.style.transform = `translate(${offsetX}px, ${offsetY}px)`;
      videoRef.current.style.transition =
        "transform 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94)";

      // Position cursor at exact center
      cursorRef.current.style.left = "50%";
      cursorRef.current.style.top = "50%";
      cursorRef.current.style.transform = "translate(-50%, -50%)";
      cursorRef.current.style.transition =
        "all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94)";
    } else {
      // Normal Mode: Cursor moves on video
      videoRef.current.style.transform = "none";
      videoRef.current.style.transition = "none";

      cursorRef.current.style.left = `${cursorX - 10}px`;
      cursorRef.current.style.top = `${cursorY - 10}px`;
      cursorRef.current.style.transform = "none";
      // Add smooth transition for cursor movement
      cursorRef.current.style.transition =
        "left 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94), top 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94)";
    }
  }, [data, isFpsMode, videoRef]);

  // Handle video seeking using frame numbers for accuracy
  useEffect(() => {
    if (!videoRef.current || data.frame_number === undefined) return;

    const video = videoRef.current;

    // Calculate target time based on frame number and video FPS
    // This ensures frame N in CSV matches frame N in video
    const videoFPS = 10; // Should match your capture FPS setting
    const targetTime = data.frame_number / videoFPS;

    // Check if we need to seek (allow small tolerance to avoid excessive seeking)
    const timeDiff = Math.abs(video.currentTime - targetTime);
    if (timeDiff > 0.05) {
      // 50ms tolerance
      setIsSeeking(true);
      setPendingData(data);
      video.currentTime = targetTime;
    } else {
      // Video is already at the right time, update display immediately
      updateDisplay();
    }
  }, [data, videoRef, updateDisplay]);

  // Handle seek completion
  const handleSeeked = useCallback(() => {
    setIsSeeking(false);
    if (pendingData) {
      setPendingData(null);
      // Update display after seeking is complete
      updateDisplay();
    }
  }, [pendingData, updateDisplay]);

  // Update display when not seeking
  useEffect(() => {
    if (!isSeeking && videoRef.current && videoRef.current.readyState >= 2) {
      updateDisplay();
    }
  }, [data, isFpsMode, updateDisplay, videoRef, isSeeking]);

  // Update display on window resize
  useEffect(() => {
    window.addEventListener("resize", updateDisplay);
    return () => window.removeEventListener("resize", updateDisplay);
  }, [updateDisplay]);

  const handleVideoLoad = () => {
    updateDisplay();
    if (onVideoLoad) onVideoLoad();
  };

  // Handle seeking start
  const handleSeeking = useCallback(() => {
    setIsSeeking(true);
  }, []);

  return (
    <div className="viewer-container">
      <div
        ref={wrapperRef}
        className={`screenshot-wrapper ${isFpsMode ? "fps-mode" : ""}`}
      >
        <video
          ref={videoRef}
          className="screenshot"
          onLoadedMetadata={handleVideoLoad}
          onSeeking={handleSeeking}
          onSeeked={handleSeeked}
          preload="auto"
          muted
        />
        <div ref={cursorRef} className="cursor-overlay">
          <div className="cursor-dot"></div>
        </div>
        {isFpsMode && (
          <>
            <div className="fps-scope-overlay">
              <div className="scope-circle">
                <div className="crosshair horizontal"></div>
                <div className="crosshair vertical"></div>
                <div className="center-dot"></div>
              </div>
            </div>
            {isBlinkEnabled && (
              <div className="blink-overlay">
                <div className="eyelid eyelid-top"></div>
                <div className="eyelid eyelid-bottom"></div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default ScreenshotDisplayVideo;
