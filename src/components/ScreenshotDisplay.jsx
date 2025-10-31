import React, { useRef, useEffect, useCallback } from "react";

function ScreenshotDisplay({ data, onImageLoad, isFpsMode, isBlinkEnabled }) {
  const imgRef = useRef(null);
  const cursorRef = useRef(null);
  const wrapperRef = useRef(null);

  const updateDisplay = useCallback(() => {
    if (!cursorRef.current || !imgRef.current || !wrapperRef.current) return;

    // Get the natural (original) size of the image
    const naturalWidth = imgRef.current.naturalWidth;
    const naturalHeight = imgRef.current.naturalHeight;

    // Get the displayed size of the image
    const displayedWidth = imgRef.current.clientWidth;
    const displayedHeight = imgRef.current.clientHeight;

    // Calculate scale factors
    const scaleX = displayedWidth / naturalWidth;
    const scaleY = displayedHeight / naturalHeight;

    // Coordinates are stored at original size but screenshot is downsampled to 50%
    // So we need to divide by 2 first, then scale to the displayed size
    const cursorX = (data.x / 2) * scaleX;
    const cursorY = (data.y / 2) * scaleY;

    if (isFpsMode) {
      // FPS Mode: Cursor stays centered, screenshot moves
      // Get the container dimensions
      const containerRect = wrapperRef.current.getBoundingClientRect();
      const centerX = containerRect.width / 2;
      const centerY = containerRect.height / 2;

      // Calculate offset to move screenshot so cursor position appears at center
      const offsetX = centerX - cursorX;
      const offsetY = centerY - cursorY;

      // Apply transform to image with smoother transition
      imgRef.current.style.transform = `translate(${offsetX}px, ${offsetY}px)`;
      imgRef.current.style.transition =
        "transform 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94)";

      // Position cursor at exact center (use 50% + transform for perfect centering)
      cursorRef.current.style.left = "50%";
      cursorRef.current.style.top = "50%";
      cursorRef.current.style.transform = "translate(-50%, -50%)";
      cursorRef.current.style.transition =
        "all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94)";
    } else {
      // Normal Mode: Cursor moves on screenshot
      imgRef.current.style.transform = "none";
      imgRef.current.style.transition = "none";

      cursorRef.current.style.left = `${cursorX - 10}px`;
      cursorRef.current.style.top = `${cursorY - 10}px`;
      cursorRef.current.style.transform = "none";
    }
  }, [data, isFpsMode]);

  useEffect(() => {
    if (imgRef.current && imgRef.current.complete) {
      updateDisplay();
    }
  }, [data, isFpsMode, updateDisplay]);

  // Update display on window resize
  useEffect(() => {
    window.addEventListener("resize", updateDisplay);
    return () => window.removeEventListener("resize", updateDisplay);
  }, [updateDisplay]);

  const handleImageLoad = () => {
    updateDisplay();
    if (onImageLoad) onImageLoad();
  };

  return (
    <div className="viewer-container">
      <div
        ref={wrapperRef}
        className={`screenshot-wrapper ${isFpsMode ? "fps-mode" : ""}`}
      >
        <img
          ref={imgRef}
          className="screenshot"
          src={data.screenshot}
          alt="Screenshot"
          onLoad={handleImageLoad}
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

export default ScreenshotDisplay;
