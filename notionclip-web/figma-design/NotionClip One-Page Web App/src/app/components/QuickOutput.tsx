export function QuickOutput() {
  return (
    <div className="space-y-6">
      {/* Summary */}
      <div>
        <div className="text-xs text-white/40 mb-3 uppercase tracking-wider">Summary</div>
        <div className="text-white/90 leading-relaxed">
          This video explores the evolution of JavaScript frameworks, focusing on the shift from client-side rendering to server-side solutions. The presenter discusses React Server Components, explaining how they reduce JavaScript bundle sizes and improve initial page load times. Key architectural decisions are compared across Next.js, Remix, and SvelteKit, with practical examples of data fetching patterns and caching strategies.
        </div>
      </div>

      {/* Takeaways */}
      <div>
        <div className="text-xs text-white/40 mb-3 uppercase tracking-wider">Key Takeaways</div>
        <div className="space-y-3">
          {[
            'Server components eliminate client-side JavaScript for static content',
            'Streaming HTML improves perceived performance for users',
            'Framework choice matters less than understanding the rendering model',
            'Edge deployment reduces latency for global users',
            'Hybrid approaches (SSR + CSR) offer the best of both worlds'
          ].map((takeaway, i) => (
            <div key={i} className="flex gap-3 items-start">
              <div className="w-6 h-6 rounded-full bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-white/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-xs text-white/60">{i + 1}</span>
              </div>
              <div className="text-white/80 text-sm leading-relaxed">{takeaway}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Topics */}
      <div>
        <div className="text-xs text-white/40 mb-3 uppercase tracking-wider">Topics Covered</div>
        <div className="flex flex-wrap gap-2">
          {[
            'React Server Components',
            'SSR vs CSR',
            'Next.js 13+',
            'Streaming',
            'Edge Computing',
            'Web Performance',
            'Framework Comparison',
            'Data Fetching'
          ].map((topic, i) => (
            <div
              key={i}
              className="px-3 py-1.5 bg-gradient-to-br from-blue-500/10 to-purple-500/10 border border-white/10 rounded-md text-xs text-white/70"
            >
              {topic}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
