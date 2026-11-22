import type {LessonId} from '../lessonArchitecture';

/** Prose owns the explanation; observations add only the selected recorded result.
 * Inline references use [[call:operation.id|purposeful label]],
 * [[cap:CAP-FAB-01|saved settings]], [[file:name.json|specific record]],
 * or [[url:<official URL>|upstream architecture]].
 */
export type TeachingSection = {
  heading?: string;
  paragraphs?: string[];
  flow?: string[];
  rows?: [string,string][];
  observation?: LessonId;
};
export type TeachingPage = {title:string;intro:string;sections:TeachingSection[]};
export type TeachingDestination =
  | {kind:'lesson';id:LessonId}
  | {kind:'concept';id:string}
  | {kind:'action';id:string;concept:string}
  | {kind:'library';id:string}
  | {kind:'operation';id:string;component:string};
