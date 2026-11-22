# Opportunity Research

Research software opportunities and decide which offers warrant further discovery, paid validation, or a production build.

The package includes the [portable plugin metadata](plugin.json), the [Codex compatibility manifest](.codex-plugin/plugin.json), and the [Opportunity Research skill](skills/opportunity-research/SKILL.md) with its five [research references](skills/opportunity-research/references/).

## Install in Codex

1. Copy this complete plugin directory, including hidden files, to `plugins/opportunity-research/` in the project where you want to run the research. The files in the package are ready to install from a checkout.
2. In the project's `.agents/plugins/marketplace.json`, add the following entry to `plugins`. When creating the marketplace file, give it a top-level `name` such as `local-repo` and a `plugins` array.

   ```json
   {
     "name": "opportunity-research",
     "source": {
       "source": "local",
       "path": "./plugins/opportunity-research"
     },
     "policy": {
       "installation": "AVAILABLE",
       "authentication": "ON_INSTALL"
     },
     "category": "Education & Research"
   }
   ```

3. Restart the ChatGPT desktop app, open the Plugins Directory, select the local marketplace, and install **Opportunity Research**. Alternatively, from the project root in a Codex CLI that supports plugin installation, run `codex plugin add opportunity-research@local-repo` using your marketplace name.

For a personal marketplace or a custom path, follow the [local marketplace instructions](https://developers.openai.com/plugins/build/plugins#install-a-local-plugin-manually).

To update, replace the copied plugin directory with the complete package from the desired Git revision. Refresh the local marketplace, update or reinstall the plugin, and start a new session. Use one installation of the skill per project to avoid duplicate discovery.

## Use

Open a session at the root of the project being researched. Select the bundled **Opportunity Research** skill from the skill picker and give it a brief. In Codex, type `$` and select the skill.

- **Start** with a brief such as “Research software opportunities in independent bike shop operations in the US.”
- **Resume** with `resume phase-01` to pick up from the saved checkpoint.
- **Revise** with `revise phase-01` and describe the changes to the brief or evidence.

The workflow writes `phases/phase-NN/report.md` and supporting notes, including `notes/status.md`, in the project. It uses web access for live research and can draw on optional local source copies under the project's `ref/` directory. When live research is unavailable, it writes a research plan based on the evidence it can verify locally.

## Maintain

Edit the canonical skill and references under `agents/skills/opportunity-research/` and the plugin metadata in `plugin.json`. Run `python3 scripts/repo.py sync` from the repository root to regenerate the bundle, Codex manifest, and ownership inventory.
