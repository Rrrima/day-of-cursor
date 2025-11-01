import React, { useState, useEffect } from "react";
import TimelineViewerVideo from "./components/TimelineViewerVideo";
import Loading from "./components/Loading";
import { MousePointer2 } from "lucide-react";

function AppVideo() {
  const [availableTags, setAvailableTags] = useState([]);
  const [selectedTag, setSelectedTag] = useState("");
  const [timelineData, setTimelineData] = useState([]);
  const [videoSrc, setVideoSrc] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch available tags on mount
  useEffect(() => {
    fetchTags();
  }, []);

  // Load data when tag is selected
  useEffect(() => {
    if (selectedTag) {
      loadData(selectedTag);
    }
  }, [selectedTag]);

  const fetchTags = async () => {
    try {
      const response = await fetch("/api/tags");
      if (!response.ok) {
        throw new Error("Failed to fetch tags");
      }
      const data = await response.json();
      setAvailableTags(data.tags);

      // Auto-select the first tag if available
      if (data.tags.length > 0) {
        setSelectedTag(data.tags[0]);
      } else {
        setError("No recordings found in __cursor_data folder");
        setLoading(false);
      }
    } catch (error) {
      console.error("Error fetching tags:", error);
      setError("Failed to load available recordings");
      setLoading(false);
    }
  };

  const loadData = async (tag) => {
    setLoading(true);
    setError(null);

    try {
      // Load CSV with video timestamps
      const response = await fetch(`/__cursor_data/mouse_positions_${tag}.csv`);
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
      setVideoSrc(`/__cursor_data/screen_capture_${tag}.webm`);
      setLoading(false);
    } catch (error) {
      console.error("Error loading data:", error);
      setError(error.message);
      setLoading(false);
    }
  };

  const handleTagChange = (event) => {
    setSelectedTag(event.target.value);
  };

  if (loading) {
    return <Loading />;
  }

  if (error) {
    return (
      <div className="loading">
        <div>Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="root-container">
      <div className="tag-selector">
        <label htmlFor="tag-select" className="tag-selector-label">
          <MousePointer2
            color="#a8a8a8"
            fill="#a8a8a8"
            strokeWidth={1}
            size={20}
          />{" "}
          <span style={{ color: "#a8a8a8" }}>is in</span>
        </label>
        <select
          id="tag-select"
          value={selectedTag}
          onChange={handleTagChange}
          className="tag-dropdown"
        >
          {availableTags.map((tag) => (
            <option key={tag} value={tag}>
              {tag}
            </option>
          ))}
        </select>
      </div>
      <TimelineViewerVideo timelineData={timelineData} videoSrc={videoSrc} />
    </div>
  );
}

export default AppVideo;
