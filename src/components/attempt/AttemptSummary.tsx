import React, { useMemo, useState, useEffect } from 'react';
import { useAttemptEngine } from '@/hooks/useAttemptEngine';
import { cn } from '@/lib/utils';

export const AttemptSummary = ({ questions }: { questions: any[] }) => {
  const { answers, activeQuestionId, setActiveQuestion } = useAttemptEngine();

  // Group questions by section
  const sections = useMemo(() => {
    const map = new Map<string, any[]>();
    questions.forEach((q) => {
      const sec = q.section || "General";
      if (!map.has(sec)) map.set(sec, []);
      map.get(sec)!.push(q);
    });
    return Array.from(map.entries()).map(([name, qs]) => ({ name, questions: qs }));
  }, [questions]);

  const [activeTab, setActiveTab] = useState<string>(
    sections.length > 0 ? sections[0].name : "General"
  );

  // When active question changes, ensure its section is the active tab
  useEffect(() => {
    if (activeQuestionId) {
      const activeQ = questions.find(q => q.id === activeQuestionId);
      if (activeQ) {
        setActiveTab(activeQ.section || "General");
      }
    }
  }, [activeQuestionId, questions]);

  const getStatusClasses = (questionId: string) => {
    const status = answers[questionId]?.status || 'NOT_VISITED';
    switch (status) {
      case 'ANSWERED':
        return 'bg-emerald-600 text-white border-emerald-700'; // Solid Green
      case 'VISITED_NOT_ANSWERED':
        return 'bg-red-600 text-white border-red-700'; // Solid Red
      case 'MARKED_FOR_REVIEW':
        return 'bg-purple-600 text-white border-purple-700'; // Solid Purple
      case 'NOT_VISITED':
      default:
        return 'bg-zinc-200 text-zinc-600 border-zinc-300 dark:bg-white/10 dark:text-[var(--text-muted)] dark:border-white/10'; // Solid Grayish
    }
  };

  const getStatusColorCircle = (status: string) => {
    switch(status) {
      case 'ANSWERED': return 'bg-emerald-600 border-emerald-700';
      case 'VISITED_NOT_ANSWERED': return 'bg-red-600 border-red-700';
      case 'MARKED_FOR_REVIEW': return 'bg-purple-600 border-purple-700';
      default: return 'bg-zinc-200 border-zinc-300 dark:bg-white/10 dark:border-white/10';
    }
  }

  const answered = Object.values(answers).filter(a => a.status === 'ANSWERED').length;
  const marked = Object.values(answers).filter(a => a.status === 'MARKED_FOR_REVIEW').length;
  const notAnswered = Object.values(answers).filter(a => a.status === 'VISITED_NOT_ANSWERED').length;
  const notVisited = Object.values(answers).filter(a => a.status === 'NOT_VISITED').length;

  const currentSectionQuestions = sections.find(s => s.name === activeTab)?.questions || [];

  return (
    <div className="flex flex-col h-full">
      {/* Legend */}
      <div className="grid grid-cols-2 gap-2 mb-4 text-[11px] font-medium text-[var(--text-secondary)]">
         <div className="flex items-center gap-2">
            <div className={cn("w-3.5 h-3.5 rounded shrink-0 border", getStatusColorCircle("ANSWERED"))}></div>
            <span>Answered</span>
         </div>
         <div className="flex items-center gap-2">
            <div className={cn("w-3.5 h-3.5 rounded shrink-0 border", getStatusColorCircle("VISITED_NOT_ANSWERED"))}></div>
            <span>Not Answered</span>
         </div>
         <div className="flex items-center gap-2">
            <div className={cn("w-3.5 h-3.5 rounded shrink-0 border", getStatusColorCircle("NOT_VISITED"))}></div>
            <span>Not Visited</span>
         </div>
         <div className="flex items-center gap-2">
            <div className={cn("w-3.5 h-3.5 rounded shrink-0 border", getStatusColorCircle("MARKED_FOR_REVIEW"))}></div>
            <span>Marked Review</span>
         </div>
      </div>

      <div className="h-px bg-[var(--border-subtle)] mb-3"></div>

      {/* Section Tabs */}
      {sections.length > 1 && (
        <div className="flex gap-1 overflow-x-auto mb-4 pb-1" style={{ scrollbarWidth: 'none' }}>
          {sections.map(section => (
            <button
              key={section.name}
              onClick={() => setActiveTab(section.name)}
              className={cn(
                "px-3 py-1.5 text-xs font-semibold whitespace-nowrap rounded-md transition-colors",
                activeTab === section.name 
                  ? "bg-[var(--accent)] text-white" 
                  : "bg-[var(--surface-2)] text-[var(--text-muted)] hover:text-[var(--text-primary)]"
              )}
            >
              {section.name}
            </button>
          ))}
        </div>
      )}

      {/* Grid of solid squares */}
      <div className="grid grid-cols-5 gap-2.5 overflow-y-auto flex-1 content-start pr-1" style={{ scrollbarWidth: 'thin', scrollbarColor: 'rgba(255,255,255,0.1) transparent' }}>
        {currentSectionQuestions.map((q) => {
          // Find absolute index of question across all questions to show correct Q number
          const absoluteIdx = questions.findIndex(globalQ => globalQ.id === q.id);
          const isActive = activeQuestionId === q.id;
          
          return (
            <button
              key={q.id}
              onClick={() => setActiveQuestion(q.id)}
              className={cn(
                "h-10 rounded shadow-sm flex items-center justify-center text-sm font-bold border transition-all duration-150 hover:opacity-80 active:scale-95",
                getStatusClasses(q.id),
                isActive && "ring-2 ring-indigo-400 ring-offset-2 ring-offset-[var(--background)] scale-110 z-10"
              )}
            >
              {absoluteIdx + 1}
            </button>
          );
        })}
      </div>
      
      {/* Global Stats footer */}
      <div className="mt-3 pt-3 border-t border-[var(--border-subtle)] grid grid-cols-2 gap-y-2 text-[11px] font-medium">
          <div className="text-[var(--text-secondary)]">Answered: <span className="text-emerald-500 font-bold ml-1">{answered}</span></div>
          <div className="text-[var(--text-secondary)]">Review: <span className="text-purple-500 font-bold ml-1">{marked}</span></div>
          <div className="text-[var(--text-secondary)]">Not Ans: <span className="text-red-500 font-bold ml-1">{notAnswered}</span></div>
          <div className="text-[var(--text-secondary)]">Not Visited: <span className="text-[var(--text-muted)] font-bold ml-1">{notVisited}</span></div>
      </div>
    </div>
  );
};
