export type TranscriptRole = 'USER' | 'ASSISTANT' | 'TOOL'

export interface ToolCallPart {
  id: string
  name: string
  args: Record<string, unknown>
}

export interface TranscriptEntryDTO {
  sequence_num: number
  role: TranscriptRole
  content: string
  tool_calls: ToolCallPart[] | null
  tool_call_id: string | null
  tool_name: string | null
  tool_inputs: Record<string, unknown> | null
  tool_status: 'success' | 'error' | null
  created_at: string
}

export interface ConversationSessionSummaryDTO {
  session_id: string
  title: string
  updated_at: string
}

export interface PaginatedSessionsDTO {
  items: ConversationSessionSummaryDTO[]
  page: number
  page_size: number
  total: number
  has_next: boolean
}
