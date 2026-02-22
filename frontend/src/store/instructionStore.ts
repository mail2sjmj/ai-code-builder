import { create } from 'zustand'

interface InstructionState {
  rawInstructions: string
  refinedPrompt: string
  isRefining: boolean
  setRawInstructions: (text: string) => void
  appendRefinedChunk: (chunk: string) => void
  setRefinedPrompt: (text: string) => void
  setIsRefining: (val: boolean) => void
  resetRefined: () => void
}

export const useInstructionStore = create<InstructionState>((set) => ({
  rawInstructions: '',
  refinedPrompt: '',
  isRefining: false,
  setRawInstructions: (text) => set({ rawInstructions: text }),
  appendRefinedChunk: (chunk) =>
    set((state) => ({ refinedPrompt: state.refinedPrompt + chunk })),
  setRefinedPrompt: (text) => set({ refinedPrompt: text }),
  setIsRefining: (val) => set({ isRefining: val }),
  resetRefined: () => set({ refinedPrompt: '' }),
}))
