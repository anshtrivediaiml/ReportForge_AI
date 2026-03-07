export const AGENTS = [
  {
    id: 'parser',
    name: 'Parser Agent',
    description: 'Analyzing project structure and extracting guidelines',
    icon: '🔍',
  },
  {
    id: 'planner',
    name: 'Planner Agent',
    description: 'Creating report structure and outline',
    icon: '📋',
  },
  {
    id: 'writer',
    name: 'Writer Agent',
    description: 'Generating content for all sections',
    icon: '✍️',
  },
  {
    id: 'builder',
    name: 'Builder Agent',
    description: 'Assembling final document',
    icon: '🏗️',
  },
] as const

export const MAX_FILE_SIZE = 100 * 1024 * 1024 // 100MB
export const CHUNK_SIZE = 5 * 1024 * 1024 // 5MB

