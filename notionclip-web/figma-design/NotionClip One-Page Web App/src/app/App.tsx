import { useState } from "react";
import { Navbar } from "./components/Navbar";
import { LeftPanel } from "./components/LeftPanel";
import { RightPanel } from "./components/RightPanel";
import { Toaster } from "./components/ui/sonner";
import { toast } from "sonner";

function App() {
  const [url, setUrl] = useState('');
  const [mode, setMode] = useState<'study' | 'work' | 'quick'>('study');
  const [isProcessing, setIsProcessing] = useState(false);
  const [hasProcessed, setHasProcessed] = useState(false);
  const [isNotionConnected, setIsNotionConnected] = useState(false);
  const [stats, setStats] = useState<{
    processingTime?: string;
    videoLength?: string;
    wordCount?: number;
    keyPointsCount?: number;
  } | null>(null);

  const handleProcess = () => {
    setIsProcessing(true);
    setHasProcessed(false);
    
    // Simulate processing
    setTimeout(() => {
      setIsProcessing(false);
      setHasProcessed(true);
      setStats({
        processingTime: '2.4s',
        videoLength: '18:42',
        wordCount: 3247,
        keyPointsCount: 12
      });
    }, 2400);
  };

  const handleConnectNotion = () => {
    // Simulate OAuth connection
    setTimeout(() => {
      setIsNotionConnected(true);
      toast.success('Successfully connected to Notion');
    }, 500);
  };

  const handleDisconnectNotion = () => {
    setIsNotionConnected(false);
    toast.success('Disconnected from Notion');
  };

  const handleSaveToNotion = () => {
    toast.success('Notes saved to Notion workspace');
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white relative overflow-hidden">
      <Toaster theme="dark" />
      {/* Dot grid background */}
      <div 
        className="fixed inset-0 opacity-[0.15]"
        style={{
          backgroundImage: 'radial-gradient(circle, rgba(255,255,255,0.15) 1px, transparent 1px)',
          backgroundSize: '24px 24px'
        }}
      />
      
      {/* Gradient orbs */}
      <div 
        className="fixed top-0 right-0 w-[600px] h-[600px] rounded-full opacity-[0.08]"
        style={{
          background: 'radial-gradient(circle, rgba(59, 130, 246, 0.5) 0%, transparent 70%)',
          filter: 'blur(80px)',
          transform: 'translate(30%, -30%)'
        }}
      />
      <div 
        className="fixed bottom-0 left-0 w-[600px] h-[600px] rounded-full opacity-[0.08]"
        style={{
          background: 'radial-gradient(circle, rgba(168, 85, 247, 0.5) 0%, transparent 70%)',
          filter: 'blur(80px)',
          transform: 'translate(-30%, 30%)'
        }}
      />

      {/* Content */}
      <div className="relative z-10">
        <Navbar 
          isNotionConnected={isNotionConnected}
          onConnectNotion={handleConnectNotion}
          onDisconnectNotion={handleDisconnectNotion}
        />
        
        <div className="pt-16 h-screen flex">
          <LeftPanel
            url={url}
            onUrlChange={setUrl}
            mode={mode}
            onModeChange={setMode}
            onProcess={handleProcess}
            isProcessing={isProcessing}
            stats={stats}
            isNotionConnected={isNotionConnected}
            onSaveToNotion={handleSaveToNotion}
            hasProcessed={hasProcessed}
          />
          
          <RightPanel
            mode={mode}
            hasProcessed={hasProcessed}
            isProcessing={isProcessing}
          />
        </div>
      </div>
    </div>
  );
}

export default App;