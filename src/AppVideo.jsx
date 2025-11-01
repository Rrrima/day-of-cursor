import React, { useState, useEffect } from "react";
import TimelineViewerVideo from "./components/TimelineViewerVideo";
import Loading from "./components/Loading";

const TAG = "rima_test";

function AppVideo() {
  const [timelineData, setTimelineData] = useState([]);
  const [videoSrc, setVideoSrc] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      // Load CSV with video timestamps
      const response = await fetch(`/__cursor_data/mouse_positions_${TAG}.csv`);
      if (!response.ok) {
        throw new Error("Failed to load CSV file");
      }

      const text = await response.text();
      const lines = text.trim().split("\n").slice(1); // Skip header

      const data = lines.map((line) => {
        const [frame_num, ts, dt, video_ts, x, y] = line.split(",");
        return {
          frame_number: parseInt(frame_num),
          timestamp: parseFloat(ts),
          datetime: dt,
          video_timestamp: parseFloat(video_ts),
          x: parseFloat(x),
          y: parseFloat(y),
        };
      });

      setTimelineData(data);
      setVideoSrc(`/__cursor_data/screen_capture_${TAG}.webm`);
      setLoading(false);
    } catch (error) {
      console.error("Error loading data:", error);
      setError(error.message);
      setLoading(false);
    }
  };

  if (loading) {
    return <Loading />;
  }

  if (error) {
    return (
      <div className="loading">
        <div>Error loading timeline data: {error}</div>
      </div>
    );
  }

  return (
    <TimelineViewerVideo timelineData={timelineData} videoSrc={videoSrc} />
  );
}

export default AppVideo;
