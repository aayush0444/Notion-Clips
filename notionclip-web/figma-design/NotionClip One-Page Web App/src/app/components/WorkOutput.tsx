import { CheckSquare, Square } from "lucide-react";
import { useState } from "react";

export function WorkOutput() {
  const [checkedItems, setCheckedItems] = useState<number[]>([]);

  const toggleCheck = (index: number) => {
    setCheckedItems(prev =>
      prev.includes(index) ? prev.filter(i => i !== index) : [...prev, index]
    );
  };

  return (
    <div className="space-y-6">
      {/* Verdict Badge */}
      <div className="flex items-center gap-4">
        <div className="inline-flex items-center gap-2 bg-green-500/20 border border-green-500/30 rounded-lg px-4 py-2.5">
          <div className="w-2 h-2 rounded-full bg-green-400"></div>
          <span className="text-green-300 font-medium">Worth Watching</span>
        </div>
        <div className="text-xs text-white/40">Based on relevance and content quality</div>
      </div>

      {/* One-liner Summary */}
      <div>
        <div className="text-xs text-white/40 mb-2 uppercase tracking-wider">Summary</div>
        <div className="text-white/90 text-base leading-relaxed">
          Comprehensive overview of modern CI/CD practices using GitHub Actions, covering automation strategies, security best practices, and deployment workflows for production environments.
        </div>
      </div>

      {/* Key Points */}
      <div>
        <div className="text-xs text-white/40 mb-3 uppercase tracking-wider">Key Points</div>
        <div className="space-y-2">
          {[
            'GitHub Actions provides native CI/CD without third-party tools',
            'Matrix builds enable testing across multiple environments simultaneously',
            'Secrets management keeps sensitive data out of workflow files',
            'Deployment gates prevent broken code from reaching production',
            'Caching dependencies reduces build times by 40-60%'
          ].map((point, i) => (
            <div key={i} className="flex gap-3 text-white/70 text-sm items-start">
              <span className="text-purple-400 mt-1">•</span>
              <span>{point}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Tools Mentioned */}
      <div>
        <div className="text-xs text-white/40 mb-3 uppercase tracking-wider">Tools Mentioned</div>
        <div className="flex flex-wrap gap-2">
          {['GitHub Actions', 'Docker', 'Kubernetes', 'Terraform', 'Slack', 'Datadog', 'Sentry'].map((tool, i) => (
            <div
              key={i}
              className="px-3 py-1.5 bg-white/5 border border-white/10 rounded-md text-xs text-white/70"
            >
              {tool}
            </div>
          ))}
        </div>
      </div>

      {/* Action Items */}
      <div>
        <div className="text-xs text-white/40 mb-3 uppercase tracking-wider">Action Items</div>
        <div className="space-y-2">
          {[
            'Set up branch protection rules for main branch',
            'Configure automated testing in pull request workflow',
            'Implement deployment preview for staging environment',
            'Add status badges to README for build visibility',
            'Review and update secrets rotation policy'
          ].map((item, i) => (
            <button
              key={i}
              onClick={() => toggleCheck(i)}
              className="w-full flex items-start gap-3 text-left text-sm text-white/70 hover:text-white/90 transition-colors group"
            >
              {checkedItems.includes(i) ? (
                <CheckSquare className="w-5 h-5 text-green-400 mt-0.5 flex-shrink-0" />
              ) : (
                <Square className="w-5 h-5 text-white/30 group-hover:text-white/50 mt-0.5 flex-shrink-0" />
              )}
              <span className={checkedItems.includes(i) ? 'line-through text-white/40' : ''}>
                {item}
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
