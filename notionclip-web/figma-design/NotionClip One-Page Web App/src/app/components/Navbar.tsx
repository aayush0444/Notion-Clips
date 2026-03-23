import { Check, X } from "lucide-react";

interface NavbarProps {
  isNotionConnected: boolean;
  onConnectNotion: () => void;
  onDisconnectNotion: () => void;
}

export function Navbar({ isNotionConnected, onConnectNotion, onDisconnectNotion }: NavbarProps) {
  return (
    <nav className="fixed top-0 left-0 right-0 h-16 border-b border-white/5 bg-[#0a0a0a]/80 backdrop-blur-xl z-50">
      <div className="max-w-[1440px] mx-auto px-8 h-full flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="text-lg font-semibold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            NotionClip
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          {isNotionConnected ? (
            <>
              <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-green-500/10 text-green-400 border border-green-500/20">
                <Check className="w-4 h-4" />
                <span className="text-sm">Connected to Notion</span>
              </div>
              <button
                onClick={onDisconnectNotion}
                className="p-2 rounded-lg bg-white/5 hover:bg-red-500/10 text-white/40 hover:text-red-400 border border-white/10 hover:border-red-500/20 transition-all"
                title="Disconnect Notion"
              >
                <X className="w-4 h-4" />
              </button>
            </>
          ) : (
            <button
              onClick={onConnectNotion}
              className="px-4 py-2 rounded-lg transition-all text-sm bg-white/5 hover:bg-white/10 text-white/90 border border-white/10 hover:border-white/20"
            >
              Connect Notion
            </button>
          )}
        </div>
      </div>
    </nav>
  );
}