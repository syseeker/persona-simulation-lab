from usersim.engine.config import ConversationSimulatorConfig
from usersim.testing import assert_hosted_parity, assert_probe_conforms


def test_probe_conforms_to_upstream_extension_contract():
    assert_probe_conforms("learning_advisor")


async def test_custom_probe_matches_native_and_hosted_user_sim():
    # Fabricated fixture; these are not source-grounded personality measurements.
    persona = {
        "uuid": "fabricated-test-record",
        "age": 35,
        "sex": "Female",
        "country": "Singapore",
        "occupation": "Clerical Worker",
        "education_level": "Secondary",
        "planning_area": "Tampines",
        "persona": "A fabricated learner interested in Excel and photography.",
    }
    config = ConversationSimulatorConfig(
        name="conversation",
        locale="en_SG",
        max_turns=2,
        max_query_attempts=1,
        max_assistant_attempts=1,
        context_compression=False,
        probe_options={"learning_advisor": {"profile_only": True}},
    )
    await assert_hosted_parity(
        "learning_advisor",
        config=config,
        persona=persona,
        data={"theme": {"description": "Find a useful learning opportunity"}},
    )
