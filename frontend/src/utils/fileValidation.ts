import appConfig from '@/config/app.config'

export interface FileValidationResult {
  valid: boolean
  error?: string
}

export function validateFile(file: File): FileValidationResult {
  const { allowedExtensions, allowedMimeTypes, maxFileSizeMb } = appConfig.upload

  // Extension check
  const dotIndex = file.name.lastIndexOf('.')
  const ext = dotIndex !== -1 ? file.name.slice(dotIndex).toLowerCase() : ''
  if (!allowedExtensions.includes(ext)) {
    return {
      valid: false,
      error: `File type "${ext || 'unknown'}" is not allowed. Please upload ${allowedExtensions.join(' or ')}.`,
    }
  }

  // MIME type check (lenient — browser MIME detection is imprecise)
  if (file.type && !allowedMimeTypes.includes(file.type)) {
    // Only warn if MIME type is set and clearly wrong — CSV may report as text/plain
    const isLikelyCsv = ext === '.csv' && (file.type.startsWith('text/') || file.type === '')
    if (!isLikelyCsv) {
      return {
        valid: false,
        error: `Unexpected file type "${file.type}". Please upload a CSV or XLSX file.`,
      }
    }
  }

  // Size check
  const maxBytes = maxFileSizeMb * 1024 * 1024
  if (file.size > maxBytes) {
    const sizeMb = (file.size / 1_048_576).toFixed(1)
    return {
      valid: false,
      error: `File size ${sizeMb} MB exceeds the ${maxFileSizeMb} MB limit.`,
    }
  }

  if (file.size === 0) {
    return { valid: false, error: 'File is empty.' }
  }

  return { valid: true }
}
