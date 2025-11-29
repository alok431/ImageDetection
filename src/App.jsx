import React, { useState, useEffect } from 'react';
import { 
  Upload, 
  AlertTriangle, 
  CheckCircle, 
  Shield, 
  Activity, 
  Lock, 
  RefreshCw, 
  X 
} from 'lucide-react';

// --- Sub-components ---

const Navbar = () => (
  <nav className="w-full py-4 px-6 flex justify-between items-center border-b border-slate-800 bg-slate-900/50 backdrop-blur-md sticky top-0 z-50">
    <div className="flex items-center space-x-2">
      <Shield className="w-8 h-8 text-indigo-500" />
      <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-cyan-400">
        Veritas AI
      </span>
    </div>
    <div className="hidden md:flex space-x-6 text-slate-400 text-sm font-medium">
      <a href="#" className="hover:text-white transition-colors">How it Works</a>
      <a href="#" className="hover:text-white transition-colors">API</a>
      <a href="#" className="hover:text-white transition-colors">About</a>
    </div>
  </nav>
);

const FeatureCard = ({ icon: Icon, title, desc }) => (
  <div className="p-6 rounded-2xl bg-slate-800/50 border border-slate-700 hover:border-indigo-500/50 transition-all">
    <Icon className="w-10 h-10 text-indigo-400 mb-4" />
    <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
    <p className="text-slate-400 text-sm leading-relaxed">{desc}</p>
  </div>
);

const ResultCard = ({ result, onReset }) => {
  const isFake = result.is_fake;
  // Ensure we have a valid number, default to 0 if missing
  const confidenceVal = result.confidence || 0; 
  const percentage = (confidenceVal * 100).toFixed(1);
  const [animatedWidth, setAnimatedWidth] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => setAnimatedWidth(percentage), 100);
    return () => clearTimeout(timer);
  }, [percentage]);

  return (
    <div className="w-full max-w-2xl bg-slate-800 rounded-3xl p-8 border border-slate-700 shadow-2xl animate-[fadeIn_0.5s_ease-out]">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h2 className="text-2xl font-bold text-white mb-1">Analysis Complete</h2>
          {result.processing_time && (
             <p className="text-slate-400 text-sm">Processed in {result.processing_time}s</p>
          )}
          {/* Show the raw label for debugging if needed */}
          <p className="text-slate-500 text-xs mt-1">Verdict: {result.label}</p>
        </div>
        <button 
          onClick={onReset}
          className="p-2 hover:bg-slate-700 rounded-full transition-colors"
        >
          <X className="w-6 h-6 text-slate-400" />
        </button>
      </div>

      <div className={`rounded-xl p-6 mb-8 border transition-colors ${
        isFake ? 'bg-red-500/10 border-red-500/20' : 'bg-emerald-500/10 border-emerald-500/20'
      }`}>
        <div className="flex items-center space-x-4 mb-4">
          {isFake ? (
            <AlertTriangle className="w-12 h-12 text-red-500" />
          ) : (
            <CheckCircle className="w-12 h-12 text-emerald-500" />
          )}
          <div>
            <h3 className={`text-3xl font-bold ${isFake ? 'text-red-400' : 'text-emerald-400'}`}>
              {isFake ? 'DEEPFAKE DETECTED' : 'LIKELY REAL'}
            </h3>
            <p className="text-slate-300">
              {isFake 
                ? 'High probability of digital manipulation artifacts found.' 
                : 'No significant digital anomalies detected.'}
            </p>
          </div>
        </div>

        {/* Confidence Meter */}
        <div className="w-full bg-slate-900 rounded-full h-4 mb-2 overflow-hidden">
          <div 
            className={`h-full transition-all duration-1000 ease-out ${isFake ? 'bg-red-500' : 'bg-emerald-500'}`}
            style={{ width: `${animatedWidth}%` }}
          />
        </div>
        <div className="flex justify-between text-xs font-mono text-slate-400">
          <span>Confidence Score</span>
          <span>{percentage}%</span>
        </div>
      </div>

      {/* Technical Details */}
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div className="bg-slate-900/50 p-4 rounded-lg">
          <span className="block text-slate-500 mb-1">Model Version</span>
          <span className="text-white font-mono">Veritas-v2.1 (MesoNet)</span>
        </div>
        <div className="bg-slate-900/50 p-4 rounded-lg">
          <span className="block text-slate-500 mb-1">Raw Output</span>
          <span className="text-white font-mono">
            {result.fake_score ? `Fake: ${(result.fake_score*100).toFixed(0)}% / Real: ${(result.real_score*100).toFixed(0)}%` : 'N/A'}
          </span>
        </div>
      </div>
    </div>
  );
};

// --- Main App Component ---

export default function App() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  
  // FIXED: Default to FALSE so you use the real API immediately
  const [useDemoMode, setUseDemoMode] = useState(false); 

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setPreview(URL.createObjectURL(selectedFile));
      setResult(null);
    }
  };

  const resetApp = () => {
    setFile(null);
    setPreview(null);
    setResult(null);
  };

  const analyzeImage = async () => {
    if (!file) return;
    setIsAnalyzing(true);
    setResult(null); // Clear previous results

    if (useDemoMode) {
      // --- Demo Logic (Simulation) ---
      console.log("Running in Demo Mode...");
      await new Promise(resolve => setTimeout(resolve, 2000)); 
      const isFake = Math.random() > 0.5;
      setResult({
        is_fake: isFake,
        confidence: 0.85 + (Math.random() * 0.14),
        processing_time: 1.2,
        label: isFake ? "AI" : "Real",
        fake_score: isFake ? 0.9 : 0.1,
        real_score: isFake ? 0.1 : 0.9
      });
      setIsAnalyzing(false);
    } else {
      // --- Real API Logic ---
      const formData = new FormData();
      formData.append("file", file);

      try {
        console.log("Sending request to Backend...");
        
        // This URL matches your Render logs
        const response = await fetch("https://imagedetection-tw7n.onrender.com/detect", {
          method: "POST",
          body: formData,
        });
        
        if (!response.ok) {
           const errorText = await response.text();
           throw new Error(`API Error: ${response.status} - ${errorText}`);
        }
        
        const data = await response.json();
        
        // --- CRITICAL DEBUGGING LOG ---
        // Press F12 in your browser and look at the Console to see this!
        console.log("Backend Response Data:", data); 
        
        setResult(data);
      } catch (error) {
        alert(`Analysis Failed: ${error.message}`);
        console.error("Full Error:", error);
      } finally {
        setIsAnalyzing(false);
      }
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-indigo-500/30 flex flex-col">
      <Navbar />

      <main className="max-w-7xl mx-auto px-6 pt-20 pb-24 flex-grow w-full">
        
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-bold tracking-wide uppercase mb-6">
            New Model v2.1 Released
          </div>
          <h1 className="text-5xl md:text-6xl font-extrabold text-white tracking-tight mb-8">
            Detect <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-cyan-400">Deepfakes</span> with Precision
          </h1>
          <p className="text-lg text-slate-400 mb-8">
            Upload any image or video frame to analyze for AI-generated manipulation artifacts.
          </p>
          
          {/* Toggle Button */}
          <div 
            className="flex items-center justify-center space-x-3 bg-slate-900/50 w-fit mx-auto px-4 py-2 rounded-full border border-slate-800 cursor-pointer select-none transition-all hover:border-indigo-500/50"
            onClick={() => setUseDemoMode(!useDemoMode)}
          >
            <span className={`text-sm font-medium transition-colors ${useDemoMode ? 'text-white' : 'text-slate-500'}`}>
              Demo Mode
            </span>
            
            <div className={`w-12 h-6 rounded-full p-1 transition-colors duration-300 relative ${useDemoMode ? 'bg-indigo-500' : 'bg-slate-700'}`}>
              <div className={`w-4 h-4 rounded-full bg-white shadow-sm transform transition-transform duration-300 ${useDemoMode ? 'translate-x-0' : 'translate-x-6'}`} />
            </div>
            
            <span className={`text-sm font-medium transition-colors ${!useDemoMode ? 'text-white' : 'text-slate-500'}`}>
              Real API
            </span>
          </div>

        </div>

        {/* Main Interface */}
        <div className="flex flex-col items-center justify-center min-h-[400px]">
          
          {!result ? (
            <div className="w-full max-w-2xl transition-all duration-300">
              {/* Dropzone */}
              <div className={`relative group border-2 border-dashed rounded-3xl p-12 text-center transition-all cursor-pointer overflow-hidden
                ${isAnalyzing ? 'border-indigo-500/50 bg-indigo-500/5 cursor-default' : 'border-slate-700 hover:border-indigo-500 hover:bg-slate-800/50 bg-slate-900'}`}
              >
                <input 
                  type="file" 
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10 disabled:cursor-default"
                  onChange={handleFileChange}
                  accept="image/*"
                  disabled={isAnalyzing}
                />
                
                {preview ? (
                  <div className="relative z-0">
                    <img src={preview} alt="Preview" className="max-h-64 mx-auto rounded-lg shadow-2xl mb-6" />
                    {isAnalyzing && (
                      <div className="absolute inset-0 bg-slate-950/60 flex items-center justify-center backdrop-blur-sm rounded-lg">
                        <div className="flex flex-col items-center">
                          <RefreshCw className="w-10 h-10 text-indigo-500 animate-spin mb-3" />
                          <span className="text-indigo-400 font-mono animate-pulse">Scanning Artifacts...</span>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="w-20 h-20 bg-slate-800 rounded-full flex items-center justify-center mx-auto group-hover:scale-110 transition-transform">
                      <Upload className="w-10 h-10 text-indigo-400" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-white">Upload an image</h3>
                      <p className="text-slate-400 mt-2">Drag and drop or click to browse</p>
                    </div>
                    <p className="text-xs text-slate-500">Supports JPG, PNG, WEBP (Max 10MB)</p>
                  </div>
                )}
              </div>

              {/* Action Button */}
              {file && !isAnalyzing && (
                <button 
                  onClick={analyzeImage}
                  className="w-full mt-6 py-4 bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white rounded-xl font-bold text-lg shadow-lg shadow-indigo-500/25 transition-all transform hover:-translate-y-1"
                >
                  Analyze Image
                </button>
              )}
            </div>
          ) : (
            <ResultCard result={result} onReset={resetApp} />
          )}

        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-3 gap-8 mt-32">
          <FeatureCard 
            icon={Activity}
            title="Artifact Analysis"
            desc="Detects subtle pixel-level inconsistencies."
          />
          <FeatureCard 
            icon={Lock}
            title="Privacy First"
            desc="Images are processed in ephemeral containers."
          />
          <FeatureCard 
            icon={RefreshCw}
            title="Real-time Processing"
            desc="Optimized PyTorch inference engine."
          />
        </div>

      </main>
    </div>
  );
}