import type { SolutionResponse } from '../types/ticket';
import type { Source } from '../components/Card/Card';

const SOURCE_STRINGS: Source[] = ['docs', 'script', 'expert', 'new_doc'];

export function getSolutionSources(solution: SolutionResponse | null | undefined): Source[] {
  if (!solution) return [];
  const record = solution.generation_source_record?.toLowerCase() ?? '';
  const found: Source[] = [];
  for (const s of SOURCE_STRINGS) {
    if (record.includes(s)) found.push(s);
  }
  return found.length > 0 ? found : ['docs'];
}
