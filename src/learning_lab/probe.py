"""A no-simulated-tools UserSim probe, registered through the public extension API."""

import json
from dataclasses import replace
from pathlib import Path

from usersim.extension import (
    BaseProbe,
    format_behavioral_profile_for_prompt,
    format_disclosure_instructions,
    format_interaction_style_instructions,
    format_persona_for_prompt,
    language_instruction,
    register_probe,
)


@register_probe
class LearningAdvisorProbe(BaseProbe):
    class Options(BaseProbe.Options):
        profile_only: bool = False
        story_id: str = 'profile-goal'

    label = "learning_advisor"
    prompt_version = "v1.2"
    assets_root = Path(__file__).parent / "assets"
    description = "A Singapore learner explores sourced courses or community classes with an advisor."

    @classmethod
    def themes(cls, locale: str) -> list[dict]:
        return [
            {"description": text}
            for text in [
                "Find a practical learning opportunity that relates to your professional ambitions.",
                "Explore a community class that relates to your hobbies and interests.",
                "Explore a digital skill that would support one of your own goals.",
            ]
        ]

    def get_user_system_prompt(self) -> str:
        overlay = self._data.get("learning_overlay", {})
        prompt = (
            "You are the simulated learner described below, talking to a Singapore course advisor. "
            "Ask for help finding an appropriate course or community class. Stay in character and respond "
            "naturally to questions. Profile narratives are synthetic context; named courses there are "
            "unverified. Do not invent your citizenship, credit balance, availability or budget. "
            "Use explicit scenario preferences when supplied; otherwise say they are undecided.\n"
            f"<profile>{format_persona_for_prompt(self._persona)}</profile>\n"
            f"Topic: {self.theme().get('description', 'Find a relevant learning opportunity')}\n"
            f"Labelled scenario assumptions: {json.dumps(overlay)}\n"
        )
        if not self.options.profile_only:
            prompt += format_behavioral_profile_for_prompt(self._profile, language=self._language) + "\n"
            prompt += format_disclosure_instructions(self._data.get("disclosure_style", "upfront")) + "\n"
            prompt += format_interaction_style_instructions(self._interaction_style) + "\n"
        if self.options.story_id == 'boardgames':
            prompt += ('\nThis test has two learner turns. First ask to learn to PLAY board games. '
                       'After the advisor replies, your NEXT message must ask whether video-game design '
                       'is the same as learning to play board games. Ask this even if no matching class '
                       'is found. Do not change that follow-up to a meetup search. Stay a learner, not an advisor.\n')
        elif self.options.story_id == 'dreamjob':
            prompt += ('\nTHREE-TURN DISCLOSURE PROTOCOL: The labelled overlay is hypothetical private simulator context. '
                       'Turn 1: say you work in retail, want sales/inventory-analysis skills and are considering the SMU SCTP data communications/visualisation certificate; ask content, duration and full fee. '
                       'Do NOT reveal salary, your spending limit or weekend availability in turn 1. '
                       'Turn 2: explicitly disclose the hypothetical monthly salary range S$2,500–3,499 and concern about the cost. '
                       'Turn 3: state an explicit total training budget of S$3,000, weekends only, and ask for shorter alternatives. '
                       'Brand interests are aspirations for learning examples, never an endorsement, a vacancy or a demand for a job. '
                       'Do not thank and finish before asking the next planned question. Remain the learner, not the advisor.\n')
        return prompt + language_instruction(self._language, self._locale)

    async def format_followup_user_instructions(self, turn_idx, state):
        if self.options.story_id == 'boardgames' and turn_idx == 1:
            return ['Now ask whether learning video-game design is the same as learning to play board games. '
                    'React naturally to the actual previous reply. Keep your original goal of playing board games. '
                    'Do not claim you have found a matching class or invent a new catalogue listing.']
        if self.options.story_id == 'dreamjob':
            if turn_idx == 1:
                return ['Now disclose: my hypothetical gross monthly salary is S$2,500–3,499. Express concern about the actual quoted course cost and ask how to think about options. Do not disclose a training budget or availability yet.']
            if turn_idx == 2:
                return ['Now state explicitly: my TOTAL TRAINING BUDGET is S$3,000, I can study on weekends only and I prefer a shorter option. Ask for alternatives for retail sales/inventory analysis. Salary is not that budget. Do not invent a listing or guarantee.']
        return []

    def user_turn_policy(self):
        policy = super().user_turn_policy()
        return replace(policy, wrap_up=False) if self.options.story_id == 'dreamjob' else policy

    def format_gate_prompt(self, user_query, conversation_history):
        prompt = super().format_gate_prompt(user_query, conversation_history)
        if self.options.story_id == 'boardgames':
            prompt += ('\nScenario-specific relevance: a learner asking whether video-game design is the same '
                       'as playing board games is an intended clarification of the original learning goal, '
                       'not an off-topic role violation. Continue to reject assistant-role language, '
                       'fourth-wall breaks and unrelated requests. Judge the candidate, do not answer it.\n')
        elif self.options.story_id == 'dreamjob':
            prompt += ('\nScenario-specific relevance: disclosing monthly salary to discuss cost, then stating an explicit '
                       'training budget and weekend-only schedule, are intended follow-ups about the same retail-learning goal. '
                       'They are not off-topic role violations. Continue checking role, language and relevance honestly.\n')
        return prompt

    def get_assistant_system_prompt(self) -> str:
        # The external advisor owns its system instructions and its real MCP tools.
        return ""
