import { ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";

export function StudyOutput() {
  const [expandedQuestions, setExpandedQuestions] = useState<number[]>([]);

  const toggleQuestion = (index: number) => {
    setExpandedQuestions(prev => 
      prev.includes(index) ? prev.filter(i => i !== index) : [...prev, index]
    );
  };

  return (
    <div className="space-y-6">
      {/* Core Concept */}
      <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-6">
        <div className="text-xs text-blue-400 mb-2 uppercase tracking-wider">Core Concept</div>
        <div className="text-white/90 leading-relaxed">
          Neural networks learn through backpropagation by adjusting weights based on the gradient of the loss function. This iterative process minimizes prediction error across training data.
        </div>
      </div>

      {/* Formula Sheet */}
      <div>
        <div className="text-xs text-white/40 mb-3 uppercase tracking-wider">Formula Sheet</div>
        <div className="bg-white/5 border border-white/10 rounded-lg p-6 font-mono text-sm space-y-4">
          <div>
            <div className="text-white/60 mb-2">Gradient Descent:</div>
            <div className="text-green-400">θ = θ - α∇J(θ)</div>
          </div>
          <div>
            <div className="text-white/60 mb-2">Mean Squared Error:</div>
            <div className="text-green-400">MSE = (1/n)Σ(y - ŷ)²</div>
          </div>
          <div>
            <div className="text-white/60 mb-2">Sigmoid Activation:</div>
            <div className="text-green-400">σ(x) = 1 / (1 + e⁻ˣ)</div>
          </div>
        </div>
      </div>

      {/* Key Facts */}
      <div>
        <div className="text-xs text-white/40 mb-3 uppercase tracking-wider">Key Facts</div>
        <div className="space-y-2">
          {[
            'Learning rate α determines step size in gradient descent',
            'Overfitting occurs when model memorizes training data',
            'Batch normalization stabilizes learning in deep networks',
            'Dropout randomly disables neurons to prevent overfitting',
            'ReLU activation is computationally efficient and prevents vanishing gradients'
          ].map((fact, i) => (
            <div key={i} className="flex gap-3 text-white/70 text-sm">
              <span className="text-white/40 font-mono">{i + 1}.</span>
              <span>{fact}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Common Mistakes */}
      <div>
        <div className="text-xs text-white/40 mb-3 uppercase tracking-wider">Common Mistakes</div>
        <div className="space-y-2">
          {[
            'Using too high learning rate causes divergence',
            'Forgetting to normalize input features',
            'Not using validation set for hyperparameter tuning'
          ].map((mistake, i) => (
            <div key={i} className="flex gap-3 text-orange-300/70 text-sm">
              <span className="text-orange-400/60">⚠</span>
              <span>{mistake}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Self-Test Questions */}
      <div>
        <div className="text-xs text-white/40 mb-3 uppercase tracking-wider">Self-Test Questions</div>
        <div className="space-y-2">
          {[
            {
              q: 'What is the purpose of the learning rate in gradient descent?',
              a: 'The learning rate controls the size of steps taken during optimization. A higher rate trains faster but may overshoot the minimum, while a lower rate is more stable but slower.'
            },
            {
              q: 'Why do we use activation functions in neural networks?',
              a: 'Activation functions introduce non-linearity, allowing networks to learn complex patterns. Without them, the network would only be able to learn linear relationships.'
            },
            {
              q: 'What is the vanishing gradient problem?',
              a: 'In deep networks, gradients can become extremely small during backpropagation, preventing earlier layers from learning effectively. This is common with sigmoid/tanh activations.'
            }
          ].map((item, i) => (
            <div key={i} className="bg-white/5 border border-white/10 rounded-lg overflow-hidden">
              <button
                onClick={() => toggleQuestion(i)}
                className="w-full px-4 py-3 flex items-center justify-between text-sm text-white/90 hover:bg-white/5 transition-colors"
              >
                <span>{item.q}</span>
                {expandedQuestions.includes(i) ? (
                  <ChevronUp className="w-4 h-4 text-white/40" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-white/40" />
                )}
              </button>
              {expandedQuestions.includes(i) && (
                <div className="px-4 pb-3 pt-1 text-sm text-white/60 leading-relaxed border-t border-white/5">
                  {item.a}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
