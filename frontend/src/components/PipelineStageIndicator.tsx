import { Check, X } from "lucide-react";

const STAGES = ["coding", "testing", "debugging", "reviewing", "done"] as const;

const STAGE_LABELS: Record<string, string> = {
  coding: "Coder",
  coding_revision: "Coder",
  testing: "Tester",
  debugging: "Debugger",
  reviewing: "Reviewer",
  done: "Done",
  coding_failed: "Coder",
  testing_failed: "Tester",
};

const AGENT_COLORS: Record<string, string> = {
  coder: "#4f6ef7",
  tester: "#8b5cf6",
  debugger: "#f59e0b",
  reviewer: "#22c55e",
  planner: "#06b6d4",
};

interface Props {
  pipelineStage: string;
  currentAgent?: string;
  retryCount?: number;
  mini?: boolean;
}

export function PipelineStageIndicator({
  pipelineStage,
  currentAgent,
  retryCount = 0,
  mini = false,
}: Props) {
  const steps = [
    { key: "coding", label: "Coder", agent: "coder" },
    { key: "testing", label: "Tester", agent: "tester" },
    { key: "debugging", label: "Debugger", agent: "debugger" },
    { key: "reviewing", label: "Reviewer", agent: "reviewer" },
  ];

  const stageOrder = [
    "coding",
    "coding_revision",
    "testing",
    "debugging",
    "reviewing",
    "done",
  ];
  const currentIdx = stageOrder.indexOf(pipelineStage);

  const getStepStatus = (stepKey: string) => {
    const stepIdx = stageOrder.indexOf(stepKey);
    if (pipelineStage === "done") return "done";
    if (pipelineStage.endsWith("_failed") && stepKey === pipelineStage.replace("_failed", "")) {
      return "failed";
    }
    if (stepIdx < currentIdx) return "done";
    if (stepIdx === currentIdx || (stepKey === "debugging" && pipelineStage === "debugging")) {
      return "active";
    }
    return "pending";
  };

  return (
    <div className={`flex items-center gap-1 ${mini ? "text-xs" : "text-sm"}`}>
      {steps.map((step, i) => {
        const status = getStepStatus(step.key);
        const color = AGENT_COLORS[step.agent];
        const isDebug = step.key === "debugging";
        if (isDebug && retryCount === 0 && status !== "active") return null;

        return (
          <div key={step.key} className="flex items-center gap-1">
            {i > 0 && <div className="w-4 h-px bg-gray-700" />}
            <div
              className={`flex items-center gap-1 px-2 py-0.5 rounded-full border transition-all ${
                status === "active"
                  ? "animate-pulse border-opacity-100"
                  : status === "done"
                    ? "opacity-70"
                    : "opacity-30"
              }`}
              style={{
                borderColor: status === "pending" ? "#333" : color,
                backgroundColor: status === "active" ? `${color}20` : "transparent",
                color: status === "pending" ? "#555" : color,
              }}
            >
              {status === "done" && <Check size={10} />}
              {status === "failed" && <X size={10} />}
              {status === "active" && (
                <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ backgroundColor: color }} />
              )}
              {!mini && <span>{step.label}</span>}
              {isDebug && retryCount > 0 && <span className="ml-1 opacity-70">({retryCount})</span>}
            </div>
          </div>
        );
      })}
    </div>
  );
}
