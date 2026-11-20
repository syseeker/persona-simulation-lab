/** Presentation order only. Source column names and stored values stay unchanged. */
export const fieldGroups: { id: string; title: string; fields: [string, string][] }[] = [
  { id: 'identity', title: 'Names and identity', fields: [
    ['first_name', 'Given name'], ['middle_name', 'Middle name'], ['last_name', 'Family name'],
    ['preferred_english_name', 'Preferred English name'], ['uuid', 'Source ID']
  ] },
  { id: 'personal', title: 'Personal details', fields: [
    ['age', 'Age'], ['sex', 'Sex'], ['marital_status', 'Marital status'],
    ['ethnic_background', 'Ethnic background'], ['cultural_background', 'Cultural background'],
    ['religion', 'Religion'], ['religious_background', 'Religious background']
  ] },
  { id: 'location', title: 'Location', fields: [
    ['country', 'Country'], ['planning_area', 'Planning area'], ['district', 'District'],
    ['postcode', 'Postcode'], ['city', 'City'], ['region', 'Region'],
    ['street_number', 'Street number'], ['street_name', 'Street name'], ['unit', 'Unit']
  ] },
  { id: 'education', title: 'Education and work', fields: [
    ['education_level', 'Education level'], ['bachelors_field', 'Bachelor’s field'],
    ['occupation', 'Occupation'], ['industry', 'Industry'], ['career_goals_and_ambitions', 'Career goals and ambitions']
  ] },
  { id: 'interests', title: 'Skills and interests', fields: [
    ['skills_and_expertise_list', 'Skills and expertise · list'], ['skills_and_expertise', 'Skills and expertise'],
    ['hobbies_and_interests_list', 'Hobbies and interests · list'], ['hobbies_and_interests', 'Hobbies and interests']
  ] },
  { id: 'narratives', title: 'Profile narratives', fields: [
    ['persona', 'Profile summary'], ['detailed_persona', 'Detailed profile'], ['professional_persona', 'Professional profile'],
    ['sports_persona', 'Sports profile'], ['arts_persona', 'Arts profile'], ['travel_persona', 'Travel profile'],
    ['culinary_persona', 'Culinary profile'], ['religious_persona', 'Religious profile'], ['finance_persona', 'Finance profile'],
    ['healthcare_persona', 'Healthcare profile']
  ] },
  { id: 'ocean', title: 'OCEAN traits', fields: [
    ['openness', 'Openness'], ['conscientiousness', 'Conscientiousness'], ['extraversion', 'Extraversion'],
    ['agreeableness', 'Agreeableness'], ['neuroticism', 'Neuroticism']
  ] }
];
const entries = fieldGroups.flatMap(group => group.fields);
const names: readonly string[] = entries.map(([key]) => key);
export function fieldLabel(name: string): string {
  return entries.find(([key]) => key === name)?.[1] ?? name.replaceAll('_', ' ');
}
export function compareFields(a: string, b: string) {
  const left = names.indexOf(a), right = names.indexOf(b);
  return (left === -1 ? names.length : left) - (right === -1 ? names.length : right) || a.localeCompare(b);
}
