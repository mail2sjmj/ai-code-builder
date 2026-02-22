import { create } from 'zustand'

interface CodeState {
  generatedCode: string
  editedCode: string
  isGenerating: boolean
  appendCodeChunk: (chunk: string) => void
  setEditedCode: (code: string) => void
  setIsGenerating: (val: boolean) => void
  resetCode: () => void
}

export const useCodeStore = create<CodeState>((set) => ({
  generatedCode: '',
  editedCode: '',
  isGenerating: false,
  appendCodeChunk: (chunk) =>
    set((state) => ({
      generatedCode: state.generatedCode + chunk,
      editedCode: state.editedCode + chunk,
    })),
  setEditedCode: (code) => set({ editedCode: code }),
  setIsGenerating: (val) => set({ isGenerating: val }),
  resetCode: () => set({ generatedCode: '', editedCode: '' }),
}))
