import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Film, Play, Search, Cpu, RefreshCw, CheckCircle, AlertTriangle, Shield, Eye, Layers, Clock, Grid, Image as ImageIcon, Sparkles } from 'lucide-react';
import { fetchLocalVideos, processLocalVideo, fetchVideoDetections, searchVideoPlates, fetchVideoSummary, fetchDiscoveredPlates } from '../services/api';

export interface LocalVideoAsset {
  video_id: string;
  filename: string;
  file_path: string;
  source_type: 'REAL_WORLD' | 'SYNTHETIC_TEST' | 'SENTINEL_LIVE';
  display_name: string;
  description: string;
  resolution: string;
  duration_seconds: number;
  fps: number;
  total_frames: number;
  processing_status: 'NOT_INDEXED' | 'PROCESSING' | 'INDEXED' | 'FAILED';
  total_detections: number;
  valid_plates_count: number;
  last_processed_at?: string;
}

export interface VideoDetectionItem {
  id: number;
  video_id: string;
  frame_number: number;
  video_timestamp_ms: number;
  track_id: number;
  vehicle_class: string;
  vehicle_confidence: number;
  bbox: [number, number, number, number];
  plate_number: string;
  plate_confidence: number;
  plate_bbox: [number, number, number, number];
  image_path?: string;
  plate_crop_path?: string;
  enhanced_plate_crop_path?: string;
}

export interface VideoSearchResult {
  detection_id: number;
  video_id: string;
  source_filename: string;
  source_type: string;
  source_display_name: string;
  frame_number: number;
  video_timestamp_ms: number;
  timestamp_seconds: number;
  vehicle_class: string;
  vehicle_confidence: number;
  bbox: [number, number, number, number];
  plate_number: string;
  plate_confidence: number;
  ocr_confidence?: number;
  image_path?: string;
  plate_crop_path?: string;
  enhanced_plate_crop_path?: string;
  supporting_frames_count?: number;
  verification_status?: string;
  preprocessing_method?: string;
  ocr_engine?: string;
  track_id?: number;
}

export interface DiscoveredPlateItem {
  plate_number: string;
  verification_status: 'VERIFIED' | 'UNREADABLE';
  vehicle_class: string;
  best_vehicle_crop?: string;
  best_plate_crop?: string;
  best_enhanced_crop?: string;
  vehicle_confidence: number;
  plate_confidence: number;
  ocr_confidence: number;
  supporting_frames_count: number;
  first_seen_timestamp_ms: number;
  last_seen_timestamp_ms: number;
  track_id: number;
  preprocessing_method: string;
  ocr_engine: string;
}

export interface VideoSummaryData {
  video_id: string;
  filename: string;
  display_name: string;
  processing_status: string;
  total_vehicles_detected: number;
  total_plates_detected: number;
  verified_plates_count: number;
  unreadable_plates_count: number;
  unique_discovered_plates: DiscoveredPlateItem[];
}

export const VideoIntelligenceView: React.FC = () => {
  const [videos, setVideos] = useState<LocalVideoAsset[]>([]);
  const [selectedVideoId, setSelectedVideoId] = useState<string>('gettyimages-1164849900-640_adpp');
  const [selectedVideo, setSelectedVideo] = useState<LocalVideoAsset | null>(null);
  
  const [processMode, setProcessMode] = useState<'full' | 'balanced' | 'fast'>('full');
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [detections, setDetections] = useState<VideoDetectionItem[]>([]);

  // Video Summary & Automatic Discovery State
  const [videoSummary, setVideoSummary] = useState<VideoSummaryData | null>(null);
  const [activeTab, setActiveTab] = useState<'discovered' | 'search'>('discovered');

  // Search & Preview state
  const [searchPlate, setSearchPlate] = useState<string>('');
  const [searchSourceId, setSearchSourceId] = useState<string>('all');
  const [searchResults, setSearchResults] = useState<VideoSearchResult[]>([]);
  const [hasSearched, setHasSearched] = useState<boolean>(false);
  const [searchMessage, setSearchMessage] = useState<string>('');
  const [previewImage, setPreviewImage] = useState<string | null>(null);

  // Video & Canvas Refs
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  // Load Videos List
  const loadVideos = async () => {
    const list = (await fetchLocalVideos()) as LocalVideoAsset[];
    if (list && list.length > 0) {
      setVideos(list);
      const current = list.find((v: LocalVideoAsset) => v.video_id === selectedVideoId) || list[0];
      setSelectedVideo(current);
      setSelectedVideoId(current.video_id);
    }
  };

  useEffect(() => {
    loadVideos();
  }, []);

  // Load Detections & Video Summary for Selected Video
  const loadVideoData = async (vId: string) => {
    const data = await fetchVideoDetections(vId);
    setDetections(data || []);

    const summary = await fetchVideoSummary(vId);
    if (summary) {
      setVideoSummary(summary);
    }
  };

  useEffect(() => {
    if (selectedVideoId) {
      loadVideoData(selectedVideoId);
      setSearchSourceId(selectedVideoId);
    }
  }, [selectedVideoId]);

  // Bucket detections into 200ms time windows for O(1) instant lookup without O(N) array filtering on every frame
  const detectionBuckets = useMemo(() => {
    const map = new Map<number, VideoDetectionItem[]>();
    for (const det of detections) {
      const bucketKey = Math.floor(det.video_timestamp_ms / 200);
      const bucket = map.get(bucketKey) || [];
      bucket.push(det);
      map.set(bucketKey, bucket);
    }
    return map;
  }, [detections]);

  // Sync Video Element with Canvas Detections
  useEffect(() => {
    const video = videoRef.current;
    const canvas = canvasRef.current;

    if (!video || !canvas) return;

    let lastRenderW = 0;
    let lastRenderH = 0;

    const renderOverlay = () => {
      if (!video || !canvas) return;

      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      const cw = video.clientWidth;
      const ch = video.clientHeight;

      // Only update canvas dimensions if actual element size changed to avoid canvas context resets and layout thrashing
      if (cw > 0 && ch > 0 && (canvas.width !== cw || canvas.height !== ch)) {
        canvas.width = cw;
        canvas.height = ch;
        lastRenderW = cw;
        lastRenderH = ch;
      }

      if (canvas.width === 0 || canvas.height === 0) {
        animationFrameRef.current = requestAnimationFrame(renderOverlay);
        return;
      }

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const currentTimeMs = video.currentTime * 1000.0;
      const bucketKey = Math.floor(currentTimeMs / 200);
      
      // O(1) retrieval from pre-computed time bucket window (±1 bucket = 300ms radius)
      const candidateDets = [
        ...(detectionBuckets.get(bucketKey - 1) || []),
        ...(detectionBuckets.get(bucketKey) || []),
        ...(detectionBuckets.get(bucketKey + 1) || [])
      ];

      const matchingDets = candidateDets.filter(
        (d) => Math.abs(d.video_timestamp_ms - currentTimeMs) < 300
      );

      const vw = video.videoWidth || 1920;
      const vh = video.videoHeight || 1080;

      const videoRatio = vw / vh;
      const canvasRatio = canvas.width / canvas.height;

      let renderW = canvas.width;
      let renderH = canvas.height;
      let offsetX = 0;
      let offsetY = 0;

      if (canvasRatio > videoRatio) {
        renderW = canvas.height * videoRatio;
        offsetX = (canvas.width - renderW) / 2.0;
      } else {
        renderH = canvas.width / videoRatio;
        offsetY = (canvas.height - renderH) / 2.0;
      }

      const scaleX = renderW / vw;
      const scaleY = renderH / vh;

      for (let i = 0; i < matchingDets.length; i++) {
        const det = matchingDets[i];
        const [x1, y1, x2, y2] = det.bbox;
        const bx = offsetX + x1 * scaleX;
        const by = offsetY + y1 * scaleY;
        const bw = (x2 - x1) * scaleX;
        const bh = (y2 - y1) * scaleY;

        ctx.strokeStyle = '#00f3ff';
        ctx.lineWidth = 2.5;
        ctx.strokeRect(bx, by, bw, bh);

        const cornerLen = Math.min(bw, bh) * 0.2;
        ctx.strokeStyle = '#00f3ff';
        ctx.lineWidth = 4;

        ctx.beginPath();
        ctx.moveTo(bx, by + cornerLen);
        ctx.lineTo(bx, by);
        ctx.lineTo(bx + cornerLen, by);
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(bx + bw - cornerLen, by);
        ctx.lineTo(bx + bw, by);
        ctx.lineTo(bx + bw, by + cornerLen);
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(bx, by + bh - cornerLen);
        ctx.lineTo(bx, by + bh);
        ctx.lineTo(bx + cornerLen, by + bh);
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(bx + bw - cornerLen, by + bh);
        ctx.lineTo(bx + bw, by + bh);
        ctx.lineTo(bx + bw, by + bh - cornerLen);
        ctx.stroke();

        if (det.plate_bbox && det.plate_bbox[2] > 0) {
          const [px1, py1, px2, py2] = det.plate_bbox;
          const pbx = offsetX + px1 * scaleX;
          const pby = offsetY + py1 * scaleY;
          const pbw = (px2 - px1) * scaleX;
          const pbh = (py2 - py1) * scaleY;

          ctx.strokeStyle = '#10b981';
          ctx.lineWidth = 2;
          ctx.strokeRect(pbx, pby, pbw, pbh);
        }

        const labelText = det.plate_number !== 'UNKNOWN' ? `🚘 ${det.vehicle_class} | 🔢 ${det.plate_number}` : `🚘 ${det.vehicle_class} | TRK-${det.track_id}`;
        ctx.font = 'bold 11px monospace';
        const textMetrics = ctx.measureText(labelText);
        const textWidth = textMetrics.width;

        ctx.fillStyle = 'rgba(12, 19, 34, 0.90)';
        ctx.fillRect(bx, by - 22, textWidth + 12, 20);

        ctx.strokeStyle = '#00f3ff';
        ctx.lineWidth = 1;
        ctx.strokeRect(bx, by - 22, textWidth + 12, 20);

        ctx.fillStyle = '#00f3ff';
        ctx.fillText(labelText, bx + 6, by - 8);
      }

      animationFrameRef.current = requestAnimationFrame(renderOverlay);
    };

    renderOverlay();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [detectionBuckets, selectedVideoId]);

  // Handle Video Select
  const handleSelectVideo = (video: LocalVideoAsset) => {
    setSelectedVideoId(video.video_id);
    setSelectedVideo(video);
    setSearchSourceId(video.video_id);
    setSearchResults([]);
    setHasSearched(false);
  };

  // Handle Process Video
  const handleProcessVideo = async () => {
    if (!selectedVideoId) return;
    setIsProcessing(true);
    const res = await processLocalVideo(selectedVideoId, processMode);
    if (res) {
      let attempts = 0;
      const interval = setInterval(async () => {
        attempts += 1;
        await loadVideoData(selectedVideoId);
        await loadVideos();
        if (attempts >= 10) {
          clearInterval(interval);
          setIsProcessing(false);
        }
      }, 3000);
    } else {
      setIsProcessing(false);
    }
  };

  // Handle Search Submit
  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!searchPlate.trim()) return;

    setHasSearched(true);
    const data = await searchVideoPlates(searchPlate, searchSourceId);
    if (data && data.results) {
      setSearchResults(data.results);
      setSearchMessage(data.message || `Found ${data.total_matches} genuine detections.`);
    } else {
      setSearchResults([]);
      setSearchMessage(`No genuine detection found for '${searchPlate}'.`);
    }
  };

  // Handle Discovered Plate Card Click
  const handleSelectDiscoveredPlate = (plateNumber: string) => {
    if (plateNumber === 'UNKNOWN') return;
    setSearchPlate(plateNumber);
    setActiveTab('search');
    searchVideoPlates(plateNumber, selectedVideoId).then((data) => {
      setHasSearched(true);
      if (data && data.results) {
        setSearchResults(data.results);
        setSearchMessage(data.message || `Found ${data.total_matches} genuine detections.`);
      }
    });
  };

  // Jump Video to Timestamp
  const handleJumpToResult = (res: VideoSearchResult) => {
    if (videoRef.current) {
      videoRef.current.currentTime = res.timestamp_seconds;
      videoRef.current.play().catch(() => {});
    }
  };

  // Current Video Overlay Counts computed efficiently
  const visibleDetsCount = useMemo(() => {
    return detections.length;
  }, [detections]);
  const visiblePlatesCount = useMemo(() => {
    return detections.filter((d) => d.plate_number !== 'UNKNOWN').length;
  }, [detections]);

  const formatTimestamp = (ms: number) => {
    const totalSecs = Math.floor(ms / 1000);
    const mins = Math.floor(totalSecs / 60);
    const secs = totalSecs % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="space-y-6">
      {/* HEADER TITLE */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-[#0c1322] border border-cyan-900/60 rounded-3xl p-6 shadow-2xl">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-cyan-500/10 border border-cyan-500/30 rounded-2xl">
              <Film className="w-6 h-6 text-cyan-400" />
            </div>
            <div>
              <h1 className="text-xl font-black text-white tracking-wide uppercase">
                Generic Video ANPR & Automatic Discovery System
              </h1>
              <p className="text-xs text-slate-400 mt-0.5">
                Automatically discovers, enhances, OCRs, and indexes vehicles & registration plates from any traffic video
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadVideos}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold bg-[#11192a] border border-slate-700 text-slate-200 hover:border-cyan-400 hover:text-cyan-400 transition-all"
          >
            <RefreshCw className="w-4 h-4" /> Refresh Catalogue
          </button>
        </div>
      </div>

      {/* VIDEO SELECTOR GRID */}
      <div className="bg-[#0c1322] border border-cyan-900/60 rounded-3xl p-6 shadow-2xl space-y-4">
        <h2 className="text-xs font-bold text-cyan-400 uppercase tracking-widest flex items-center gap-2">
          <Layers className="w-4 h-4 text-cyan-400" /> Local Traffic Video Library ({videos.length} Available)
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
          {videos.map((vid) => {
            const isSelected = vid.video_id === selectedVideoId;
            return (
              <div
                key={vid.video_id}
                onClick={() => handleSelectVideo(vid)}
                className={`cursor-pointer rounded-2xl p-4 border transition-all flex flex-col justify-between ${
                  isSelected
                    ? 'bg-[#111c33] border-cyan-400 shadow-lg shadow-cyan-500/10'
                    : 'bg-[#0f1729] border-slate-800 hover:border-cyan-500/50 hover:bg-[#131f38]'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-wider bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
                      {vid.source_type}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded text-[9px] font-bold ${
                        vid.processing_status === 'INDEXED'
                          ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                          : 'bg-amber-500/20 text-amber-400 border border-amber-500/40'
                      }`}
                    >
                      {vid.processing_status}
                    </span>
                  </div>

                  <h3 className="font-bold text-xs text-white line-clamp-1">{vid.display_name}</h3>
                  <p className="text-[11px] text-slate-400 line-clamp-2 mt-1">{vid.description}</p>
                </div>

                <div className="mt-3 pt-3 border-t border-slate-800/80 grid grid-cols-2 gap-2 text-[10px]">
                  <div>
                    <span className="text-slate-500 block">Resolution</span>
                    <span className="font-mono text-slate-200">{vid.resolution}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Detections</span>
                    <span className="font-mono text-cyan-400 font-bold">{vid.total_detections}</span>
                  </div>
                </div>

                {isSelected && (
                  <div className="mt-3 flex items-center gap-2 text-xs text-cyan-400 font-bold">
                    <CheckCircle className="w-4 h-4 text-cyan-400" /> Active Video Source
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* MAIN VIDEO PLAYER WITH REAL-TIME CANVAS AI OVERLAY */}
      {selectedVideo && (
        <div className="bg-[#0c1322] border border-cyan-900/60 rounded-3xl p-6 shadow-2xl space-y-4">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-1 rounded-md text-[10px] font-black uppercase bg-cyan-500/20 text-cyan-400 border border-cyan-500/40">
                  {selectedVideo.source_type}
                </span>
                <h2 className="text-lg font-bold text-white">{selectedVideo.display_name}</h2>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                {selectedVideo.filename} • {selectedVideo.resolution} • {selectedVideo.fps} FPS
              </p>
            </div>

            {/* PROCESSING CONTROLS */}
            <div className="flex items-center gap-3">
              <select
                value={processMode}
                onChange={(e) => setProcessMode(e.target.value as any)}
                className="bg-[#11192a] border border-slate-700 text-slate-200 text-xs rounded-xl px-3 py-2 focus:border-cyan-400 outline-none"
              >
                <option value="full">Full Accuracy (Every Frame)</option>
                <option value="balanced">Balanced Mode (Every 2nd Frame)</option>
                <option value="fast">Fast Mode (Every 5th Frame)</option>
              </select>

              <button
                onClick={handleProcessVideo}
                disabled={isProcessing}
                className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-gradient-to-r from-cyan-500 to-blue-600 text-black hover:brightness-110 transition-all disabled:opacity-50"
              >
                <RefreshCw className={`w-4 h-4 ${isProcessing ? 'animate-spin' : ''}`} />
                {isProcessing ? 'Processing Video...' : 'Run AI Indexing'}
              </button>
            </div>
          </div>

          {/* VIDEO CANVAS CONTAINER */}
          <div className="relative w-full rounded-2xl overflow-hidden bg-black border border-slate-800 shadow-inner group">
            {/* HTML5 VIDEO ELEMENT WITH HIGH-PERFORMANCE STREAMING */}
            <video
              ref={videoRef}
              src={`/api/videos/${selectedVideo.video_id}/stream`}
              controls
              playsInline
              preload="metadata"
              className="w-full h-auto max-h-[520px] object-contain mx-auto"
            />

            {/* HTML5 CANVAS OVERLAY */}
            <canvas
              ref={canvasRef}
              className="absolute top-0 left-0 w-full h-full pointer-events-none"
            />

            {/* HUD STATUS OVERLAY BADGE */}
            <div className="absolute top-4 left-4 bg-black/80 backdrop-blur-md border border-cyan-500/40 rounded-xl px-3.5 py-2 flex items-center gap-3 text-xs shadow-xl">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping" />
              <div>
                <div className="text-[10px] font-black text-cyan-400 uppercase tracking-widest">
                  AI ANALYSIS OVERLAY ACTIVE
                </div>
                <div className="text-[11px] text-slate-300 font-mono">
                  Indexed Detections: <span className="text-white font-bold">{visibleDetsCount}</span> | Recognized Plates:{' '}
                  <span className="text-cyan-400 font-bold">{visiblePlatesCount}</span>
                </div>
              </div>
            </div>

            {/* VIDEO PLAYBACK SPEED CONTROL BAR */}
            <div className="absolute bottom-4 right-4 bg-black/85 backdrop-blur-md border border-cyan-500/50 rounded-xl px-3 py-1.5 flex items-center gap-2 text-xs shadow-xl z-20">
              <span className="text-[10px] font-mono text-cyan-400 font-bold uppercase tracking-wider">Speed:</span>
              {[0.5, 0.75, 1.0, 1.5, 2.0].map((rate) => (
                <button
                  key={rate}
                  onClick={() => {
                    if (videoRef.current) videoRef.current.playbackRate = rate;
                  }}
                  className="bg-[#0e1726] hover:bg-cyan-500 hover:text-black text-cyan-300 font-mono font-extrabold text-[11px] px-2 py-0.5 rounded border border-cyan-800/80 transition-all cursor-pointer"
                >
                  {rate}x
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* VIDEO SUMMARY TELEMETRY & AUTOMATIC DISCOVERY SECTION */}
      {videoSummary && (
        <div className="bg-[#0c1322] border border-cyan-900/60 rounded-3xl p-6 shadow-2xl space-y-6">
          {/* TOP SUMMARY STATS KPI CARDS */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-[#0f172a] border border-cyan-900/50 rounded-2xl p-4">
              <span className="text-[10px] font-bold text-slate-400 uppercase block">Total Vehicles Detected</span>
              <span className="text-2xl font-black text-white font-mono mt-1 block">
                {videoSummary.total_vehicles_detected}
              </span>
            </div>

            <div className="bg-[#0f172a] border border-cyan-900/50 rounded-2xl p-4">
              <span className="text-[10px] font-bold text-slate-400 uppercase block">Total Plates Cropped</span>
              <span className="text-2xl font-black text-cyan-400 font-mono mt-1 block">
                {videoSummary.total_plates_detected}
              </span>
            </div>

            <div className="bg-[#0f172a] border border-emerald-900/50 rounded-2xl p-4">
              <span className="text-[10px] font-bold text-emerald-400 uppercase block">Verified Plates (OCR)</span>
              <span className="text-2xl font-black text-emerald-400 font-mono mt-1 block">
                {videoSummary.verified_plates_count}
              </span>
            </div>

            <div className="bg-[#0f172a] border border-amber-900/50 rounded-2xl p-4">
              <span className="text-[10px] font-bold text-amber-400 uppercase block">Unreadable / Blurred</span>
              <span className="text-2xl font-black text-amber-400 font-mono mt-1 block">
                {videoSummary.unreadable_plates_count}
              </span>
            </div>
          </div>

          {/* TWO PRIMARY WORKFLOW NAVIGATION BUTTONS */}
          <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
            <button
              onClick={() => setActiveTab('discovered')}
              className={`flex items-center gap-2 px-5 py-3 rounded-2xl text-xs font-black transition-all ${
                activeTab === 'discovered'
                  ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-black shadow-lg shadow-cyan-500/20'
                  : 'bg-[#11192a] border border-slate-700 text-slate-300 hover:border-cyan-400'
              }`}
            >
              <Grid className="w-4 h-4" /> Show All Discovered Plates ({videoSummary.unique_discovered_plates.length})
            </button>

            <button
              onClick={() => setActiveTab('search')}
              className={`flex items-center gap-2 px-5 py-3 rounded-2xl text-xs font-black transition-all ${
                activeTab === 'search'
                  ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-black shadow-lg shadow-cyan-500/20'
                  : 'bg-[#11192a] border border-slate-700 text-slate-300 hover:border-cyan-400'
              }`}
            >
              <Search className="w-4 h-4" /> Search Plate Number
            </button>
          </div>

          {/* TAB 1: SHOW ALL DISCOVERED PLATES GRID */}
          {activeTab === 'discovered' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-cyan-400" /> Automatically Discovered Plate Candidates
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Click any discovered plate to search all matching frames and timeline positions
                  </p>
                </div>
              </div>

              {videoSummary.unique_discovered_plates.length === 0 ? (
                <div className="bg-[#101726] border border-slate-800 rounded-2xl p-8 text-center space-y-2">
                  <AlertTriangle className="w-8 h-8 text-amber-400 mx-auto" />
                  <div className="text-sm font-bold text-amber-300">No Plates Discovered Yet</div>
                  <div className="text-xs text-slate-400">
                    Click "Run AI Indexing" above to process this video through YOLO vehicle detection and EasyOCR.
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                  {videoSummary.unique_discovered_plates.map((item, idx) => {
                    const isVerified = item.verification_status === 'VERIFIED';
                    return (
                      <div
                        key={idx}
                        onClick={() => handleSelectDiscoveredPlate(item.plate_number)}
                        className={`bg-[#0f1729] border rounded-2xl p-4 transition-all hover:bg-[#131f38] cursor-pointer group space-y-3 ${
                          isVerified
                            ? 'border-cyan-900/60 hover:border-cyan-400'
                            : 'border-amber-900/40 hover:border-amber-400'
                        }`}
                      >
                        {/* CARD BADGE & TRACK ID */}
                        <div className="flex items-center justify-between">
                          <span
                            className={`px-2.5 py-0.5 rounded text-[10px] font-black uppercase tracking-wider ${
                              isVerified
                                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                                : 'bg-amber-500/20 text-amber-400 border border-amber-500/40'
                            }`}
                          >
                            {isVerified ? 'VERIFIED PLATE' : 'UNREADABLE PLATE'}
                          </span>
                          <span className="text-[11px] font-mono text-cyan-400 font-bold">
                            Track ID #{item.track_id}
                          </span>
                        </div>

                        {/* 3 CROP IMAGES: VEHICLE, PLATE, ENHANCED */}
                        <div className="grid grid-cols-3 gap-2 my-2">
                          <div
                            onClick={(e) => {
                              e.stopPropagation();
                              setPreviewImage(
                                item.best_vehicle_crop
                                  ? item.best_vehicle_crop.startsWith('http')
                                    ? item.best_vehicle_crop
                                    : `${item.best_vehicle_crop.startsWith('/') ? '' : '/'}${item.best_vehicle_crop}`
                                  : '/static/crops/vehicle_crop_sample.jpg'
                              );
                            }}
                            className="relative h-20 rounded-lg overflow-hidden border border-slate-700 bg-black group/img cursor-pointer"
                          >
                            <img
                              src={
                                item.best_vehicle_crop
                                  ? item.best_vehicle_crop.startsWith('http')
                                    ? item.best_vehicle_crop
                                    : `${item.best_vehicle_crop.startsWith('/') ? '' : '/'}${item.best_vehicle_crop}`
                                  : '/static/crops/vehicle_crop_sample.jpg'
                              }
                              alt="Vehicle Crop"
                              className="w-full h-full object-cover group-hover/img:scale-105 transition-transform duration-300"
                              onError={(e) => {
                                (e.target as HTMLImageElement).src = '/static/crops/vehicle_crop_sample.jpg';
                              }}
                            />
                            <span className="absolute bottom-0.5 left-0.5 bg-black/85 text-[8px] text-cyan-300 font-bold px-1 py-0.5 rounded">
                              Vehicle
                            </span>
                          </div>

                          <div
                            onClick={(e) => {
                              e.stopPropagation();
                              setPreviewImage(
                                item.best_plate_crop
                                  ? item.best_plate_crop.startsWith('http')
                                    ? item.best_plate_crop
                                    : `${item.best_plate_crop.startsWith('/') ? '' : '/'}${item.best_plate_crop}`
                                  : '/static/crops/plate_crop_sample.jpg'
                              );
                            }}
                            className="relative h-20 rounded-lg overflow-hidden border border-emerald-500/40 bg-black group/img cursor-pointer"
                          >
                            <img
                              src={
                                item.best_plate_crop
                                  ? item.best_plate_crop.startsWith('http')
                                    ? item.best_plate_crop
                                    : `${item.best_plate_crop.startsWith('/') ? '' : '/'}${item.best_plate_crop}`
                                  : '/static/crops/plate_crop_sample.jpg'
                              }
                              alt="Plate Crop"
                              className="w-full h-full object-contain p-1 group-hover/img:scale-105 transition-transform duration-300"
                              onError={(e) => {
                                (e.target as HTMLImageElement).src = '/static/crops/plate_crop_sample.jpg';
                              }}
                            />
                            <span className="absolute bottom-0.5 left-0.5 bg-black/85 text-[8px] text-emerald-300 font-bold px-1 py-0.5 rounded">
                              Plate
                            </span>
                          </div>

                          <div
                            onClick={(e) => {
                              e.stopPropagation();
                              setPreviewImage(
                                item.best_enhanced_crop
                                  ? item.best_enhanced_crop.startsWith('http')
                                    ? item.best_enhanced_crop
                                    : `${item.best_enhanced_crop.startsWith('/') ? '' : '/'}${item.best_enhanced_crop}`
                                  : '/static/crops/plate_crop_sample.jpg'
                              );
                            }}
                            className="relative h-20 rounded-lg overflow-hidden border border-cyan-400/50 bg-black group/img cursor-pointer"
                          >
                            <img
                              src={
                                item.best_enhanced_crop
                                  ? item.best_enhanced_crop.startsWith('http')
                                    ? item.best_enhanced_crop
                                    : `${item.best_enhanced_crop.startsWith('/') ? '' : '/'}${item.best_enhanced_crop}`
                                  : '/static/crops/plate_crop_sample.jpg'
                              }
                              alt="Enhanced Crop"
                              className="w-full h-full object-contain p-1 group-hover/img:scale-105 transition-transform duration-300"
                              onError={(e) => {
                                (e.target as HTMLImageElement).src = '/static/crops/plate_crop_sample.jpg';
                              }}
                            />
                            <span className="absolute bottom-0.5 left-0.5 bg-black/85 text-[8px] text-cyan-300 font-bold px-1 py-0.5 rounded">
                              Enhanced
                            </span>
                          </div>
                        </div>

                        {/* PLATE NUMBER & UNREADABLE REASON */}
                        <div>
                          <div className="text-xl font-black text-white tracking-wide font-mono">
                            {item.plate_number}
                          </div>
                          {!isVerified && (
                            <p className="text-[10px] text-amber-400 mt-1 italic">
                              "Plate detected, but image quality is insufficient for verified OCR."
                            </p>
                          )}
                        </div>

                        {/* TELEMETRY METRICS */}
                        <div className="grid grid-cols-2 gap-2 bg-[#080d17] p-2.5 rounded-xl text-[10px] text-slate-300">
                          <div>
                            <span className="text-slate-500 block">Vehicle Class</span>
                            <span className="font-semibold text-slate-200">{item.vehicle_class}</span>
                          </div>
                          <div>
                            <span className="text-slate-500 block">Supporting Frames</span>
                            <span className="font-bold text-cyan-400">{item.supporting_frames_count} frames</span>
                          </div>
                          <div>
                            <span className="text-slate-500 block">OCR Conf.</span>
                            <span className="font-semibold text-emerald-400">
                              {Math.round(item.plate_confidence * 100)}%
                            </span>
                          </div>
                          <div>
                            <span className="text-slate-500 block">Timeline Window</span>
                            <span className="font-mono text-slate-300">
                              {formatTimestamp(item.first_seen_timestamp_ms)} - {formatTimestamp(item.last_seen_timestamp_ms)}
                            </span>
                          </div>
                        </div>

                        <div className="text-[9px] text-slate-500 font-mono truncate">
                          Enhancement: {item.preprocessing_method}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* TAB 2: SEARCH ANY DETECTED PLATE */}
          {activeTab === 'search' && (
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Search className="w-4 h-4 text-cyan-400" /> Search Detected Plates (Video-Scoped)
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Type any plate registration number to query matching video detections in {selectedVideo.display_name}
                </p>
              </div>

              <form onSubmit={handleSearch} className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="text-xs text-slate-400 font-semibold mb-1 block">Target Video Source</label>
                  <select
                    value={searchSourceId}
                    onChange={(e) => setSearchSourceId(e.target.value)}
                    className="w-full bg-[#11192a] border border-slate-700 text-slate-200 text-xs rounded-xl px-4 py-3 focus:border-cyan-400 outline-none"
                  >
                    <option value="all">🔍 Search All Local Video Sources</option>
                    {videos.map((v) => (
                      <option key={v.video_id} value={v.video_id}>
                        {v.display_name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-xs text-slate-400 font-semibold mb-1 block">Plate Registration Number</label>
                  <input
                    type="text"
                    placeholder="Search box starts empty — type plate or click from Discovered list"
                    value={searchPlate}
                    onChange={(e) => setSearchPlate(e.target.value)}
                    className="w-full bg-[#11192a] border border-slate-700 text-slate-200 text-xs rounded-xl px-4 py-3 focus:border-cyan-400 outline-none font-mono uppercase"
                  />
                </div>

                <div className="flex items-end">
                  <button
                    type="submit"
                    className="w-full flex items-center justify-center gap-2 py-3 rounded-xl text-xs font-bold bg-gradient-to-r from-cyan-500 to-blue-600 text-black hover:brightness-110 transition-all shadow-lg shadow-cyan-500/20"
                  >
                    <Search className="w-4 h-4 text-black" /> Search Source Database
                  </button>
                </div>
              </form>

              {/* SEARCH RESULTS */}
              {hasSearched && (
                <div className="space-y-4 pt-2">
                  <div className="text-xs font-bold text-slate-300 border-b border-slate-800 pb-2">
                    Search Results ({searchResults.length} matches found)
                  </div>

                  {searchResults.length === 0 ? (
                    <div className="bg-[#101726] border border-slate-800 rounded-2xl p-6 text-center space-y-2">
                      <AlertTriangle className="w-8 h-8 text-amber-400 mx-auto" />
                      <div className="text-sm font-bold text-amber-300">{searchMessage}</div>
                      <div className="text-xs text-slate-400 max-w-md mx-auto">
                        Only genuine AI detections are indexed. If a plate is too blurred or distant in wide-angle footage,
                        no fabricated match is returned.
                      </div>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {searchResults.map((res) => (
                        <div
                          key={res.detection_id}
                          className="bg-[#0f1729] border border-cyan-900/60 rounded-2xl p-4 hover:border-cyan-400 transition-all hover:bg-[#131f38] group space-y-3"
                        >
                          <div className="flex items-center justify-between">
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-cyan-500/20 text-cyan-300">
                              {res.source_type}
                            </span>
                            <span className="text-[11px] font-mono text-cyan-400 font-bold flex items-center gap-1">
                              <Clock className="w-3 h-3 text-cyan-400" /> {res.timestamp_seconds}s
                            </span>
                          </div>

                          {/* 3 CROP IMAGES */}
                          <div className="grid grid-cols-3 gap-2 my-2">
                            <div
                              onClick={() =>
                                setPreviewImage(
                                  res.image_path
                                    ? res.image_path.startsWith('http')
                                      ? res.image_path
                                      : `${res.image_path.startsWith('/') ? '' : '/'}${res.image_path}`
                                    : '/static/crops/vehicle_crop_sample.jpg'
                                )
                              }
                              className="relative h-20 rounded-lg overflow-hidden border border-slate-700 bg-black cursor-pointer group/img"
                            >
                              <img
                                src={
                                  res.image_path
                                    ? res.image_path.startsWith('http')
                                      ? res.image_path
                                      : `${res.image_path.startsWith('/') ? '' : '/'}${res.image_path}`
                                    : '/static/crops/vehicle_crop_sample.jpg'
                                }
                                alt="Vehicle Crop"
                                className="w-full h-full object-cover group-hover/img:scale-105 transition-transform duration-300"
                                onError={(e) => {
                                  (e.target as HTMLImageElement).src = '/static/crops/vehicle_crop_sample.jpg';
                                }}
                              />
                              <span className="absolute bottom-0.5 left-0.5 bg-black/80 text-[8px] text-cyan-300 font-bold px-1 py-0.5 rounded">
                                Vehicle
                              </span>
                            </div>

                            <div
                              onClick={() =>
                                setPreviewImage(
                                  res.plate_crop_path
                                    ? res.plate_crop_path.startsWith('http')
                                      ? res.plate_crop_path
                                      : `${res.plate_crop_path.startsWith('/') ? '' : '/'}${res.plate_crop_path}`
                                    : '/static/crops/plate_crop_sample.jpg'
                                )
                              }
                              className="relative h-20 rounded-lg overflow-hidden border border-emerald-500/40 bg-black cursor-pointer group/img"
                            >
                              <img
                                src={
                                  res.plate_crop_path
                                    ? res.plate_crop_path.startsWith('http')
                                      ? res.plate_crop_path
                                      : `${res.plate_crop_path.startsWith('/') ? '' : '/'}${res.plate_crop_path}`
                                    : '/static/crops/plate_crop_sample.jpg'
                                }
                                alt="Plate Crop"
                                className="w-full h-full object-contain p-1 group-hover/img:scale-105 transition-transform duration-300"
                                onError={(e) => {
                                  (e.target as HTMLImageElement).src = '/static/crops/plate_crop_sample.jpg';
                                }}
                              />
                              <span className="absolute bottom-0.5 left-0.5 bg-black/80 text-[8px] text-emerald-300 font-bold px-1 py-0.5 rounded">
                                Plate
                              </span>
                            </div>

                            <div
                              onClick={() =>
                                setPreviewImage(
                                  res.enhanced_plate_crop_path
                                    ? res.enhanced_plate_crop_path.startsWith('http')
                                      ? res.enhanced_plate_crop_path
                                      : `${res.enhanced_plate_crop_path.startsWith('/') ? '' : '/'}${res.enhanced_plate_crop_path}`
                                    : '/static/crops/plate_crop_sample.jpg'
                                )
                              }
                              className="relative h-20 rounded-lg overflow-hidden border border-cyan-400/50 bg-black cursor-pointer group/img"
                            >
                              <img
                                src={
                                  res.enhanced_plate_crop_path
                                    ? res.enhanced_plate_crop_path.startsWith('http')
                                      ? res.enhanced_plate_crop_path
                                      : `${res.enhanced_plate_crop_path.startsWith('/') ? '' : '/'}${res.enhanced_plate_crop_path}`
                                    : '/static/crops/plate_crop_sample.jpg'
                                }
                                alt="Enhanced Crop"
                                className="w-full h-full object-contain p-1 group-hover/img:scale-105 transition-transform duration-300"
                                onError={(e) => {
                                  (e.target as HTMLImageElement).src = '/static/crops/plate_crop_sample.jpg';
                                }}
                              />
                              <span className="absolute bottom-0.5 left-0.5 bg-black/80 text-[8px] text-cyan-300 font-bold px-1 py-0.5 rounded">
                                Enhanced
                              </span>
                            </div>
                          </div>

                          <div>
                            <div className="text-xs text-slate-400 truncate">{res.source_display_name}</div>
                            <div className="text-lg font-black text-white tracking-wide font-mono mt-0.5">
                              {res.plate_number}
                            </div>
                          </div>

                          <div className="grid grid-cols-2 gap-2 bg-[#080d17] p-2 rounded-xl text-[10px] text-slate-300">
                            <div>
                              <span className="text-slate-500 block">Vehicle Class</span>
                              <span className="font-semibold text-slate-200">{res.vehicle_class}</span>
                            </div>
                            <div>
                              <span className="text-slate-500 block">OCR Conf.</span>
                              <span className="font-semibold text-emerald-400">
                                {Math.round(res.plate_confidence * 100)}%
                              </span>
                            </div>
                          </div>

                          <button
                            onClick={() => handleJumpToResult(res)}
                            className="w-full text-center text-[10px] text-cyan-400 font-bold group-hover:underline flex items-center justify-center gap-1 pt-1"
                          >
                            <Play className="w-3 h-3 text-cyan-400" /> Jump to Video Timestamp & Overlay
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* PHOTO PREVIEW MODAL */}
      {previewImage && (
        <div
          className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 cursor-pointer"
          onClick={() => setPreviewImage(null)}
        >
          <div
            className="bg-[#0f172a] border border-cyan-500/40 rounded-2xl p-4 max-w-3xl max-h-[85vh] overflow-hidden space-y-3 relative shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <span className="text-xs font-bold text-cyan-400 uppercase tracking-wider">
                HIGH-RESOLUTION DETECTION PHOTO EVIDENCE
              </span>
              <button
                onClick={() => setPreviewImage(null)}
                className="text-slate-400 hover:text-white text-sm font-bold px-2 py-1 bg-slate-800 rounded-lg"
              >
                ✕ Close
              </button>
            </div>
            <div className="flex items-center justify-center bg-black rounded-xl p-2 max-h-[70vh] overflow-auto">
              <img
                src={previewImage}
                alt="High Resolution Evidence"
                className="max-h-[65vh] w-auto object-contain rounded-lg shadow-lg"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
