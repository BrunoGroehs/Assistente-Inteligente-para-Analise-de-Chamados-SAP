export type Source = { url: string; title: string; numbers: number[] }
export type Attachment = { id: string; reference: string; title: string }
export type Support = {
  product?: string; product_version?: string; system_id?: string; client?: string;
  system_role?: string; component?: string; reporter?: string; customer?: string;
  reported_at?: string; application?: string; business_impact?: string;
  expected_result?: string; actual_result?: string; error_message?: string;
  steps_to_reproduce?: string[]; actions_taken?: string[]; attachments?: string[];
  priority?: string; sap_case_number?: string;
}
export type Order = {
  purchase_order: string; item: string; material: string; plant: string; storage_location: string;
  ordered: string; received: string; remaining?: string; unit: string; delivery_completed?: boolean;
}
export type Case = Attachment & {
  description: string; status: string; priority_label: string; support?: Support; order?: Order | null;
}
export type Message = {
  id: string; role: string; content: string; error: boolean; attachment?: Attachment | null; proposal_id?: string;
  correction?: Correction | null;
  details: {
    confidence?: string; confidence_reason?: string; facts: { text: string; numbers: number[] }[];
    hypotheses: string[]; missing_information: string[]; next_steps: string[];
    sources: Source[]; consulted_sources: Source[]; policies: { number: number; title: string }[];
    transactions: Order[]; steps: string[]; latency_ms?: number;
  };
}
export type Correction = {
  operation: 'registrar_recebimento_simulado' | 'atualizar_status_chamado'; ticket: string; expires_at: string;
  purchase_order?: string; item?: string; material?: string; unit?: string; max_quantity?: string;
}
export type CorrectionValues = { quantity?: string; posting_date?: string; status?: string }
export type Proposal = {
  id: string; ticket: string; state: string; expires_at: string; phrase: string;
  effect: { operation: string; purchase_order?: string; item?: string; material?: string; plant?: string;
    storage_location?: string; posting_date?: string; quantity?: string; unit?: string;
    ticket?: string; before: string; after: string };
  result: { message?: string; receipt_id?: string };
}
export type Snapshot = { cases: Case[]; messages: Message[]; proposals: Proposal[]; server_time?: string }
export type ProgressEvent = { type: 'progress' | 'completed' | 'error' | 'heartbeat'; label?: string; message?: string; state?: string }
