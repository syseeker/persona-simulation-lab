# Managed-agent template

`agent.yaml` remains the base input for the [Platform packager](../../integrations/platform/package_agent.py). It is reusable backend configuration, separate from the retired browser dashboard.

The skill path is a repository-local symbolic link to the canonical [runtime skill](../../runtime-skills/course-advisor/SKILL.md). This removes a stale duplicate. The packager copies that canonical file into the generated package as an ordinary file, so deployed images do not depend on the repository symlink.

The [local validator](../../integrations/helix/validate_agent.py) loads and plans the template without registering, deploying or invoking a model. Historical template and skill bytes remain in the [v0.2 source snapshot](../../docs/history/v0.2/INDEX.md).
