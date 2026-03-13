export type Difficulty = 'easy' | 'medium' | 'high';

export type Product = 'ExampleCo PropertySuite Affordable';

export type Category =
  | 'Advance Property Date'
  | 'Certifications'
  | 'Close Bank Deposit'
  | 'General'
  | 'Gross Rent Change'
  | 'HAP / Voucher Processing'
  | 'Move-In'
  | 'Move-Out'
  | 'Repayment Plan'
  | 'Security Deposit'
  | 'TRACS File'
  | 'Unit Transfer'
  | 'Units / Move-In-Out'
  | 'Waitlist';

export type Module =
  | 'Accounting'
  | 'Accounting / Banking'
  | 'Accounting / Date Advance'
  | 'Accounting / Deposits'
  | 'Activity - Account History'
  | 'Affordable / HAP'
  | 'Affordable / Repayments'
  | 'Affordable / TRACS'
  | 'Certifications'
  | 'Close period status'
  | 'Compliance / Certifications'
  | 'Compliance / Rent'
  | 'Final Account Statements'
  | 'General'
  | 'HAP / Vouchers'
  | 'HUD'
  | 'Other'
  | 'People - Household Members'
  | 'Residents / Move-In'
  | 'Residents / Move-Out'
  | 'Residents / Transfers'
  | 'TRACS / File Transmission'
  | 'Units / Move-In-Out'
  | 'Verification Letters'
  | 'Waitlist';

export type SolutionStatus = 'pending' | 'processed' | 'done';

export interface TicketCreate {
  question: string;
  difficulty?: Difficulty;
  product?: Product;
  category?: Category;
  module?: Module;
}

export interface TicketResponse {
  id: string;
  user_id: string;
  question: string;
  difficulty: Difficulty;
  product: Product;
  category: Category;
  module: Module;
  created_at?: string;
}

export interface TicketUpdate {
  question?: string | null;
  difficulty?: Difficulty | null;
  product?: Product | null;
  category?: Category | null;
  module?: Module | null;
}

export interface SolutionCreate {
  ticket_id: string;
  script?: string | null;
  target_title?: string | null;
  generation_source_record?: string | null;
  status?: SolutionStatus;
  text?: string | null;
}

export interface SolutionResponse {
  id: string;
  ticket_id: string;
  script: string | null;
  target_title: string | null;
  generation_source_record: string | null;
  status: SolutionStatus;
  text: string | null;
}

export interface SolutionUpdate {
  script?: string | null;
  target_title?: string | null;
  generation_source_record?: string | null;
  status?: SolutionStatus | null;
  text?: string | null;
}

export interface TicketSummary extends TicketResponse {
  solution_status?: SolutionStatus;
  solution_preview?: string | null;
  solution_sources?: ('script' | 'docs' | 'expert' | 'new_doc')[];
}

export type SolutionSource = 'script' | 'docs' | 'expert' | 'new_doc';

export const PRODUCT_OPTIONS: { value: Product; label: string }[] = [
  { value: 'ExampleCo PropertySuite Affordable', label: 'ExampleCo PropertySuite Affordable' },
];

export const CATEGORY_OPTIONS: { value: Category; label: string }[] = [
  'Advance Property Date',
  'Certifications',
  'Close Bank Deposit',
  'General',
  'Gross Rent Change',
  'HAP / Voucher Processing',
  'Move-In',
  'Move-Out',
  'Repayment Plan',
  'Security Deposit',
  'TRACS File',
  'Unit Transfer',
  'Units / Move-In-Out',
  'Waitlist',
].map((v) => ({ value: v as Category, label: v }));

export const MODULE_OPTIONS: { value: Module; label: string }[] = [
  'Accounting',
  'Accounting / Banking',
  'Accounting / Date Advance',
  'Accounting / Deposits',
  'Activity - Account History',
  'Affordable / HAP',
  'Affordable / Repayments',
  'Affordable / TRACS',
  'Certifications',
  'Close period status',
  'Compliance / Certifications',
  'Compliance / Rent',
  'Final Account Statements',
  'General',
  'HAP / Vouchers',
  'HUD',
  'Other',
  'People - Household Members',
  'Residents / Move-In',
  'Residents / Move-Out',
  'Residents / Transfers',
  'TRACS / File Transmission',
  'Units / Move-In-Out',
  'Verification Letters',
  'Waitlist',
].map((v) => ({ value: v as Module, label: v }));

export const DIFFICULTY_OPTIONS: { value: Difficulty; label: string }[] = [
  { value: 'easy', label: 'Easy' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
];
