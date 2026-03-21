"use client"

import { motion } from 'framer-motion'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { BookOpen, Briefcase, Zap } from 'lucide-react'

const features = [
  {
    mode: "Study Mode",
    subtitle: "For lectures and courses",
    icon: BookOpen,
    colorClass: "text-blue-400",
    borderClass: "border-l-[3px] border-l-blue-400 border-t-white/10 border-r-white/10 border-b-white/10",
    items: [
      "Formula sheet with variable definitions",
      "Key facts scaled to video length",
      "Self-test questions with hidden answers",
      "Timestamped facts you can verify"
    ]
  },
  {
    mode: "Work Mode",
    subtitle: "For professional content",
    icon: Briefcase,
    colorClass: "text-purple-400",
    borderClass: "border-l-[3px] border-l-purple-400 border-t-white/10 border-r-white/10 border-b-white/10",
    items: [
      "Watch or Skip verdict with reasoning",
      "Tools and frameworks mentioned",
      "Decisions your team should consider",
      "Specific next actions"
    ]
  },
  {
    mode: "Quick Mode",
    subtitle: "For casual watching",
    icon: Zap,
    colorClass: "text-green-400",
    borderClass: "border-l-[3px] border-l-green-400 border-t-white/10 border-r-white/10 border-b-white/10",
    items: [
      "The gist in under two minutes",
      "Most surprising takeaways",
      "Conversational, no jargon"
    ]
  }
]

export function FeatureCards() {
  return (
    <div className="py-24 sm:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
          {features.map((feature, i) => (
            <motion.div
              key={feature.mode}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              transition={{ duration: 0.5, delay: i * 0.15 }}
              className="h-full"
            >
              <Card className={`h-full ${feature.borderClass}`}>
                <CardHeader>
                  <feature.icon className={`h-8 w-8 mb-4 ${feature.colorClass}`} />
                  <CardTitle>{feature.mode}</CardTitle>
                  <p className="text-sm text-muted mt-1">{feature.subtitle}</p>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-3 mt-2">
                    {feature.items.map((item, j) => (
                      <li key={j} className="flex items-start">
                        <span className="mr-3 mt-1.5 block h-1.5 w-1.5 rounded-full bg-white/30 shrink-0" />
                        <span className="text-sm text-white/80 leading-relaxed">{item}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  )
}
