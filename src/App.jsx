import React, { useState, useEffect, useRef, useCallback } from "react";
import TimelineViewer from "./components/TimelineViewer";
import Loading from "./components/Loading";

const TAG = "Literature_infospace";

function App() {
  const [timelineData, setTimelineData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const response = await fetch(`/__cursor_data/mouse_positions_${TAG}.csv`);
      if (!response.ok) {
        throw new Error("Failed to load CSV file");
      }

      const text = await response.text();
      const lines = text.trim().split("\n").slice(1); // Skip header

      const data = lines
        .map((line) => {
          const [ts, dt, x, y, screenshotPath] = line.split(",");
          return {
            timestamp: parseFloat(ts),
            datetime: dt,
            x: parseFloat(x),
            y: parseFloat(y),
            screenshot: screenshotPath,
          };
        })
        .filter((item) => item.screenshot); // Filter out any empty entries

      setTimelineData(data);
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

  return <TimelineViewer timelineData={timelineData} />;
}

export default App;
