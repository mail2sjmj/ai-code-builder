import { useInstructionStore } from '@/store/instructionStore'

const MAX_LENGTH = 5000
const PLACEHOLDER = `Describe what you want to do with your data, step by step.

Example:
1. Filter rows where Status is "Active"
2. Group by Region
3. Calculate average Revenue per group
4. Sort descending by average Revenue
5. Keep only Region and AverageRevenue columns`

export function RawInstructionBox() {
  const { rawInstructions, setRawInstructions } = useInstructionStore()
  const remaining = MAX_LENGTH - rawInstructions.length

  return (
    <div className="flex flex-1 flex-col gap-2">
      <label className="text-sm font-semibold text-foreground">Your Instructions</label>
      <textarea
        value={rawInstructions}
        onChange={(e) => setRawInstructions(e.target.value.slice(0, MAX_LENGTH))}
        placeholder={PLACEHOLDER}
        className="flex-1 resize-y rounded-lg border bg-background p-3 font-mono text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring min-h-[220px]"
        spellCheck={false}
      />
      <p className={`text-right text-xs ${remaining < 100 ? 'text-destructive' : 'text-muted-foreground'}`}>
        {rawInstructions.length}/{MAX_LENGTH}
      </p>
    </div>
  )
}
